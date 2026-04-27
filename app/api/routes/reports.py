from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission_dependency, tenant_ids
from app.api.schemas import CreateReportRequest, GeneratedReportResponse
from app.auth.service import AuthContext
from app.config.settings import Settings, get_settings
from app.db.repositories import (
    create_generated_report,
    get_generated_report,
    list_extracted_records,
    list_generated_reports,
    list_validation_errors,
)
from app.db.session import get_db_session
from app.reports.builders import build_records_csv_rows, build_summary_report
from app.reports.exporters import write_csv_report, write_json_report

router = APIRouter(prefix="/reports", tags=["reports"])


def to_report_response(report) -> GeneratedReportResponse:
    return GeneratedReportResponse(
        report_id=UUID(report.id),
        report_type=report.report_type,
        status=report.status,
        parameters=report.parameters,
        storage_path=report.storage_path,
        created_at=report.created_at,
    )


@router.post("", response_model=GeneratedReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: CreateReportRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext, Depends(require_permission_dependency("report:write"))],
) -> GeneratedReportResponse:
    organization_id, workspace_id = tenant_ids(context)
    records = await list_extracted_records(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    validation_errors = await list_validation_errors(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )

    if request.report_type == "summary":
        payload = build_summary_report(records, validation_errors)
        if request.format == "json":
            storage_path = write_json_report(settings.reports_dir, payload)
        else:
            storage_path = write_csv_report(settings.reports_dir, payload["records"])
    else:
        rows = build_records_csv_rows(records)
        if request.format == "json":
            storage_path = write_json_report(settings.reports_dir, {"records": rows})
        else:
            storage_path = write_csv_report(settings.reports_dir, rows)

    report = await create_generated_report(
        session,
        report_type=request.report_type,
        organization_id=organization_id,
        workspace_id=workspace_id,
        parameters={"format": request.format},
        storage_path=str(storage_path),
    )
    return to_report_response(report)


@router.get("", response_model=list[GeneratedReportResponse])
async def get_reports(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext, Depends(require_permission_dependency("report:read"))],
) -> list[GeneratedReportResponse]:
    organization_id, workspace_id = tenant_ids(context)
    reports = await list_generated_reports(
        session,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    return [to_report_response(report) for report in reports]


@router.get("/{report_id}", response_model=GeneratedReportResponse)
async def get_report(
    report_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext, Depends(require_permission_dependency("report:read"))],
) -> GeneratedReportResponse:
    organization_id, workspace_id = tenant_ids(context)
    report = await get_generated_report(
        session,
        report_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' was not found.",
        )
    return to_report_response(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    context: Annotated[AuthContext, Depends(require_permission_dependency("report:read"))],
) -> FileResponse:
    organization_id, workspace_id = tenant_ids(context)
    report = await get_generated_report(
        session,
        report_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' was not found.",
        )
    if not report.storage_path or not Path(report.storage_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file for '{report_id}' was not found.",
        )
    return FileResponse(path=report.storage_path, filename=Path(report.storage_path).name)
