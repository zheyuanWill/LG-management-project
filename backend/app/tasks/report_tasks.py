from datetime import date

from loguru import logger

from app.async_utils import run_async
from app.celery_app import celery_app


@celery_app.task(name="app.tasks.report_tasks.generate_daily_report_task")
def generate_daily_report_task(project_id: int, report_date_str: str) -> dict:
    report_date = date.fromisoformat(report_date_str)
    logger.info(f"Starting daily report generation: project={project_id}, date={report_date}")

    async def _run():
        from app.db import async_session_maker
        from app.models.report import DailyReport
        from app.services.report_service import generate_daily_report

        async with async_session_maker() as db:
            try:
                report_data = await generate_daily_report(db, project_id, report_date)

                existing = await db.execute(
                    DailyReport.__table__.select().where(
                        DailyReport.project_id == project_id,
                        DailyReport.report_date == report_date,
                    )
                )
                existing_report = existing.fetchone()

                if existing_report:
                    await db.execute(
                        DailyReport.__table__.update().where(
                            DailyReport.project_id == project_id,
                            DailyReport.report_date == report_date,
                        ).values(
                            completed_items=report_data.get("completed_items"),
                            tomorrow_plan=report_data.get("tomorrow_plan"),
                            risk_alert=report_data.get("risk_alert"),
                        )
                    )
                    logger.info(f"Updated daily report for project {project_id} on {report_date}")
                else:
                    await db.execute(
                        DailyReport.__table__.insert().values(
                            project_id=project_id,
                            report_date=report_date,
                            completed_items=report_data.get("completed_items"),
                            tomorrow_plan=report_data.get("tomorrow_plan"),
                            risk_alert=report_data.get("risk_alert"),
                        )
                    )
                    logger.info(f"Created daily report for project {project_id} on {report_date}")

                await db.commit()
                return {"status": "success", "project_id": project_id, "report_date": str(report_date)}
            except Exception as e:
                logger.error(f"Failed to generate daily report: {e}")
                await db.rollback()
                raise

    try:
        return run_async(_run())
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.report_tasks.generate_weekly_report_task")
def generate_weekly_report_task(project_id: int, week_start_str: str) -> dict:
    week_start = date.fromisoformat(week_start_str)
    logger.info(f"Starting weekly report generation: project={project_id}, week_start={week_start}")

    async def _run():
        from app.db import async_session_maker
        from app.models.report import WeeklyReport
        from app.services.report_service import generate_weekly_report

        async with async_session_maker() as db:
            try:
                report_data = await generate_weekly_report(db, project_id, week_start)

                week_end = report_data.get("week_end_date", week_start)

                existing = await db.execute(
                    WeeklyReport.__table__.select().where(
                        WeeklyReport.project_id == project_id,
                        WeeklyReport.week_start_date == week_start,
                    )
                )
                existing_report = existing.fetchone()

                if existing_report:
                    await db.execute(
                        WeeklyReport.__table__.update().where(
                            WeeklyReport.project_id == project_id,
                            WeeklyReport.week_start_date == week_start,
                        ).values(
                            summary=report_data.get("summary"),
                            next_week_plan=report_data.get("next_week_plan"),
                        )
                    )
                    logger.info(f"Updated weekly report for project {project_id} week of {week_start}")
                else:
                    await db.execute(
                        WeeklyReport.__table__.insert().values(
                            project_id=project_id,
                            week_start_date=week_start,
                            week_end_date=week_end,
                            summary=report_data.get("summary"),
                            next_week_plan=report_data.get("next_week_plan"),
                        )
                    )
                    logger.info(f"Created weekly report for project {project_id} week of {week_start}")

                await db.commit()
                return {"status": "success", "project_id": project_id, "week_start": str(week_start)}
            except Exception as e:
                logger.error(f"Failed to generate weekly report: {e}")
                await db.rollback()
                raise

    try:
        return run_async(_run())
    except Exception as e:
        logger.error(f"Weekly report generation failed: {e}")
        return {"status": "failed", "error": str(e)}