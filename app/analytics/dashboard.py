from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    AnalyticsBlockedJobResponse,
    AnalyticsCostResponse,
    AnalyticsDashboardResponse,
    AnalyticsKpiResponse,
    AnalyticsRankedItemResponse,
    AnalyticsTrendPointResponse,
)
from app.config.settings import Settings
from app.db.models import (
    ExtractedRecord,
    ExtractionErrorLog,
    GeneratedReport,
    ProcessingJob,
    UploadedFile,
    ValidationError,
)


async def build_analytics_dashboard(
    session: AsyncSession,
    settings: Settings,
) -> AnalyticsDashboardResponse:
    now = datetime.now(UTC)
    files = await _list_all(session, UploadedFile)
    jobs = await _list_all(session, ProcessingJob)
    records = await _list_all(session, ExtractedRecord)
    validation_errors = await _list_all(session, ValidationError)
    extraction_errors = await _list_all(session, ExtractionErrorLog)
    reports = await _list_all(session, GeneratedReport)

    record_by_id = {record.id: record for record in records}
    file_by_id = {file.id: file for file in files}

    processed_today = _count_since(files, now.replace(hour=0, minute=0, second=0, microsecond=0))
    processed_week = _count_since(files, now - timedelta(days=7))
    processed_month = _count_since(
        files,
        now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
    )
    failed_jobs = sum(1 for job in jobs if job.status == "failed")
    blocked_jobs = [
        job
        for job in jobs
        if job.status in {"failed", "running"} and _age_hours(now, job.updated_at) >= 0
    ]
    avg_confidence = _average(
        [record.confidence for record in records if record.confidence is not None]
    )
    validation_rate = (
        len(validation_errors) / len(records)
        if records
        else 0
    )

    validation_by_type = Counter(
        (
            record_by_id.get(error.record_id).record_type
            if error.record_id in record_by_id
            else "unknown"
        )
        for error in validation_errors
    )
    error_sources = Counter()
    for error in validation_errors:
        record = record_by_id.get(error.record_id or "")
        source = record.vendor_name if record and record.vendor_name else "Unknown source"
        error_sources[source] += 1
    for error in extraction_errors:
        file = file_by_id.get(error.file_id or "")
        source = file.original_filename if file else "Unknown source"
        error_sources[source] += 1

    confidence_by_day: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.confidence is None:
            continue
        confidence_by_day[_date_key(record.created_at)].append(record.confidence * 100)

    retry_hotspots = Counter(
        f"{error.stage}: {error.error_type}" for error in extraction_errors if error.retryable
    )
    repeated_failures = Counter(job.file_id for job in jobs if job.status == "failed")
    cost = _estimate_llm_cost(records, settings)
    report_counts = Counter(report.report_type for report in reports)

    analyst_notes = _build_analyst_notes(
        processed_week=processed_week,
        failed_jobs=failed_jobs,
        blocked_jobs=len(blocked_jobs),
        avg_confidence=avg_confidence,
        validation_rate=validation_rate,
        retry_count=sum(retry_hotspots.values()),
        estimated_cost=cost.estimated_cost_usd,
    )

    return AnalyticsDashboardResponse(
        generated_at=now,
        kpis=[
            AnalyticsKpiResponse(
                label="Files processed today",
                value=str(processed_today),
                detail=f"{processed_week} in the last 7 days",
                trend=_trend_label(processed_today, processed_week / 7 if processed_week else 0),
                status="healthy" if processed_today > 0 else "watch",
            ),
            AnalyticsKpiResponse(
                label="Extraction accuracy",
                value=f"{avg_confidence * 100:.1f}%" if records else "N/A",
                detail=f"{len(records)} structured records",
                trend="schema confidence average",
                status="healthy" if avg_confidence >= 0.85 else "watch",
            ),
            AnalyticsKpiResponse(
                label="Validation burden",
                value=f"{validation_rate * 100:.1f}%" if records else "0%",
                detail=f"{len(validation_errors)} findings across records",
                trend="findings per extracted record",
                status="risk" if validation_rate > 0.5 else "healthy",
            ),
            AnalyticsKpiResponse(
                label="Blocked jobs",
                value=str(len(blocked_jobs)),
                detail=f"{failed_jobs} failed jobs total",
                trend="requires operator review" if blocked_jobs else "no blockers",
                status="risk" if blocked_jobs else "healthy",
            ),
            AnalyticsKpiResponse(
                label="Estimated LLM cost",
                value=f"${cost.estimated_cost_usd:.4f}",
                detail=f"{cost.estimated_input_tokens:,} input tokens estimated",
                trend="mock records excluded from billable cost",
                status="healthy",
            ),
        ],
        processed_volume={
            "today": processed_today,
            "last_7_days": processed_week,
            "month_to_date": processed_month,
            "all_time": len(files),
        },
        validation_failures_by_document_type=_ranked(
            validation_by_type,
            suffix="validation findings",
        ),
        error_sources=_ranked(error_sources, suffix="error events"),
        extraction_accuracy_over_time=[
            AnalyticsTrendPointResponse(
                date=date,
                value=round(_average(values), 2),
                detail=f"{len(values)} records",
            )
            for date, values in sorted(confidence_by_day.items())
        ][-14:],
        retry_hotspots=_ranked(retry_hotspots, suffix="retry attempts"),
        blocked_jobs=[
            AnalyticsBlockedJobResponse(
                job_id=job.id,
                file_id=job.file_id,
                status=job.status,
                pipeline=job.pipeline,
                age_hours=round(_age_hours(now, job.updated_at), 2),
                error_message=job.error_message,
            )
            for job in sorted(blocked_jobs, key=lambda item: item.updated_at, reverse=True)[:8]
        ],
        llm_cost=cost,
        business_reports=_ranked(report_counts, suffix="generated reports"),
        analyst_notes=analyst_notes + _repeated_failure_notes(repeated_failures, file_by_id),
    )


async def _list_all(session: AsyncSession, model: type) -> list[Any]:
    result = await session.execute(select(model))
    return list(result.scalars().all())


def _count_since(items: list[Any], threshold: datetime) -> int:
    return sum(1 for item in items if _as_utc(item.created_at) >= threshold)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _age_hours(now: datetime, value: datetime) -> float:
    return (now - _as_utc(value)).total_seconds() / 3600


def _date_key(value: datetime) -> str:
    return _as_utc(value).date().isoformat()


def _average(values: list[float | None]) -> float:
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return 0
    return sum(clean_values) / len(clean_values)


def _ranked(counter: Counter, *, suffix: str) -> list[AnalyticsRankedItemResponse]:
    return [
        AnalyticsRankedItemResponse(label=str(label), value=float(value), detail=suffix)
        for label, value in counter.most_common(6)
    ]


def _trend_label(current: int, baseline: float) -> str:
    if baseline == 0 and current > 0:
        return "new activity"
    if current >= baseline:
        return "above recent pace"
    return "below recent pace"


def _estimate_llm_cost(
    records: list[ExtractedRecord],
    settings: Settings,
) -> AnalyticsCostResponse:
    input_tokens = 0
    output_tokens = 0
    billable_records = 0
    mock_records = 0

    for record in records:
        raw_payload = record.raw_payload or {}
        provider = raw_payload.get("provider")
        if provider == "mock":
            mock_records += 1
            continue
        billable_records += 1
        metadata = (
            raw_payload.get("record", {})
            .get("raw_fields", {})
            .get("metadata", {})
        )
        character_count = metadata.get("character_count")
        if isinstance(character_count, int | float):
            input_tokens += int(character_count / 4)
        else:
            input_tokens += 1200
        output_tokens += max(300, int(len(str(record.normalized_payload)) / 4))

    estimated_cost = (
        (input_tokens / 1000) * settings.llm_input_cost_per_1k_tokens
        + (output_tokens / 1000) * settings.llm_output_cost_per_1k_tokens
    )
    return AnalyticsCostResponse(
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_cost_usd=round(estimated_cost, 6),
        billable_records=billable_records,
        mock_records=mock_records,
    )


def _build_analyst_notes(
    *,
    processed_week: int,
    failed_jobs: int,
    blocked_jobs: int,
    avg_confidence: float,
    validation_rate: float,
    retry_count: int,
    estimated_cost: float,
) -> list[str]:
    notes = []
    if processed_week == 0:
        notes.append(
            "No documents were processed in the last 7 days; validate ingestion readiness."
        )
    if avg_confidence and avg_confidence < 0.85:
        notes.append("Average extraction confidence is below the production review threshold.")
    if validation_rate > 0.5:
        notes.append(
            "Validation findings are high; prioritize document-type-specific extraction prompts."
        )
    if blocked_jobs or failed_jobs:
        notes.append(
            "Blocked or failed jobs exist; review retry and parser error details before "
            "onboarding clients."
        )
    if retry_count:
        notes.append(
            "Retries are occurring; monitor whether they cluster by provider, document type, "
            "or source."
        )
    if estimated_cost > 5:
        notes.append(
            "Estimated LLM cost is material; consider batching, caching, or cheaper "
            "extraction models."
        )
    if not notes:
        notes.append(
            "Pipeline health is stable based on current document volume and validation signals."
        )
    return notes


def _repeated_failure_notes(
    failures_by_file_id: Counter,
    file_by_id: dict[str, UploadedFile],
) -> list[str]:
    notes = []
    for file_id, count in failures_by_file_id.most_common(2):
        if count < 2:
            continue
        file = file_by_id.get(file_id)
        label = file.original_filename if file else file_id
        notes.append(f"{label} has failed {count} times; treat it as a repeat failure source.")
    return notes
