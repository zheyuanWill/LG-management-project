from loguru import logger

from app.async_utils import run_async
from app.celery_app import celery_app


@celery_app.task(name="app.tasks.risk_tasks.detect_risks_task")
def detect_risks_task(project_id: int) -> dict:
    logger.info(f"Starting risk detection: project_id={project_id}")

    async def _run():
        from app.db import async_session_maker
        from app.models.report import RiskEvent
        from app.services.risk_service import detect_risks

        async with async_session_maker() as db:
            try:
                new_risks = await detect_risks(db, project_id)

                for risk_data in new_risks:
                    await db.execute(
                        RiskEvent.__table__.insert().values(
                            project_id=project_id,
                            title=risk_data["title"],
                            detail=risk_data.get("detail"),
                            risk_level=risk_data.get("risk_level", "info"),
                            resolved=False,
                        )
                    )

                await db.commit()
                logger.info(
                    f"Risk detection completed: project={project_id}, new_risks={len(new_risks)}"
                )
                return {
                    "status": "success",
                    "project_id": project_id,
                    "new_risks_count": len(new_risks),
                    "risks": new_risks,
                }
            except Exception as e:
                logger.error(f"Risk detection failed: {e}")
                await db.rollback()
                raise

    try:
        return run_async(_run())
    except Exception as e:
        logger.error(f"Risk detection task failed: {e}")
        return {"status": "failed", "error": str(e)}