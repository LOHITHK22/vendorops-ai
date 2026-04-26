from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.dashboard import build_analytics_dashboard
from app.api.schemas import AnalyticsDashboardResponse
from app.config.settings import Settings, get_settings
from app.db.session import get_db_session

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard_analytics(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsDashboardResponse:
    return await build_analytics_dashboard(session, settings)
