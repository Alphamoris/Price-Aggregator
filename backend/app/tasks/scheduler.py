from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import async_session_maker
from app.services.asset_service import AssetService
from app.utils.logging import get_logger
from app.config import get_settings

settings = get_settings()
logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_data_job():
    logger.info("scheduled_refresh_started")
    
    async with async_session_maker() as session:
        try:
            asset_service = AssetService(session)
            results = await asset_service.refresh_all_data()
            await session.commit()
            
            logger.info(
                "scheduled_refresh_complete",
                crypto_success=results["crypto_success"],
                stock_success=results["stock_success"],
                crypto_count=results["crypto_count"],
                stock_count=results["stock_count"]
            )
        except Exception as e:
            await session.rollback()
            logger.error("scheduled_refresh_error", error=str(e))


def start_scheduler():
    if scheduler.running:
        return
    
    scheduler.add_job(
        refresh_data_job,
        trigger=IntervalTrigger(minutes=settings.scheduler_refresh_interval_minutes),
        id="refresh_data",
        name="Refresh asset data from external APIs",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=None
    )
    
    scheduler.add_job(
        refresh_data_job,
        id="refresh_data_initial",
        name="Initial data refresh",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info(
        "scheduler_started",
        interval_minutes=settings.scheduler_refresh_interval_minutes
    )


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
