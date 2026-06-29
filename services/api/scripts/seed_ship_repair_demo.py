"""
Seed ship repair demo data for V2.
Run: docker exec lgm-api python scripts/seed_ship_repair_demo.py
"""
import asyncio
from datetime import date, timedelta
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '.')

from app.core.config import settings
from app.models.user import User
from app.models.ship_repair import Project, Task, DailyLog, Issue, ProjectStatus, TaskStatus


async def seed_ship_repair_demo():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        pm_user = (await db.execute(select(User).where(User.username == 'pm'))).scalar_one()

        existing = (await db.execute(select(Project).limit(1))).scalar_one_or_none()
        if existing:
            print('Ship repair v2 demo data already exists, skipping.')
            return

        project = Project(
            project_name='主机大修项目',
            vessel_name='MV PACIFIC',
            ship_owner='Pacific Shipping',
            shipyard='舟山某船厂',
            dock_in_date=date.today() - timedelta(days=2),
            dock_out_date=date.today() + timedelta(days=20),
            repair_specification='主机拆检、曲轴测量、缸套检查与更换、主机回装；同时完成船体局部钢板修复与涂装。',
            status=ProjectStatus.IN_PROGRESS,
            created_by=pm_user.id,
        )
        db.add(project)
        await db.flush()

        tasks = [
            Task(project_id=project.id, task_name='主机拆解', description='按规范拆检主机主要部件', category='ENGINE', status=TaskStatus.COMPLETED, ai_generated=True, sort_order=1),
            Task(project_id=project.id, task_name='曲轴测量', description='完成曲轴尺寸和磨损测量', category='ENGINE', status=TaskStatus.COMPLETED, ai_generated=True, sort_order=2),
            Task(project_id=project.id, task_name='缸套更换', description='更换磨损严重的缸套', category='ENGINE', status=TaskStatus.IN_PROGRESS, ai_generated=True, sort_order=3),
            Task(project_id=project.id, task_name='主机回装', description='完成回装并试车', category='ENGINE', status=TaskStatus.PENDING, ai_generated=True, sort_order=4),
            Task(project_id=project.id, task_name='船体局部钢板修复', description='局部换板与探伤', category='OTHER', status=TaskStatus.IN_PROGRESS, ai_generated=True, sort_order=5),
        ]
        db.add_all(tasks)
        await db.flush()

        log1 = DailyLog(
            project_id=project.id,
            log_date=date.today() - timedelta(days=1),
            reporter_id=pm_user.id,
            work_done='完成主机拆解和曲轴测量。',
            discoveries='发现2号缸套磨损严重，需更换。',
            tomorrow_plan='安排缸套拆除并确认备件到货时间。',
            notes='现场配合正常。',
            ai_processed=True,
            ai_summary='已识别质量问题并更新部分任务状态。',
        )
        log2 = DailyLog(
            project_id=project.id,
            log_date=date.today(),
            reporter_id=pm_user.id,
            work_done='开始处理2号缸套更换，同时推进局部钢板修复。',
            discoveries='供应商通知缸套备件将延期3天到货。',
            tomorrow_plan='继续钢板修复并协调备件供应。',
            notes='需持续关注工期影响。',
            ai_processed=False,
        )
        db.add_all([log1, log2])
        await db.flush()

        issues = [
            Issue(
                project_id=project.id,
                task_id=tasks[2].id,
                daily_log_id=log1.id,
                issue_type='QUALITY',
                title='2号缸套磨损严重',
                description='测量发现磨损超限，需要更换。',
                severity='HIGH',
                status='OPEN',
                ai_generated=True,
            ),
            Issue(
                project_id=project.id,
                task_id=tasks[2].id,
                daily_log_id=log2.id,
                issue_type='SCHEDULE',
                title='缸套备件延期到货',
                description='供应商通知延期3天，可能影响主机回装。',
                severity='HIGH',
                status='OPEN',
                ai_generated=True,
            ),
        ]
        db.add_all(issues)

        await db.commit()
        print(f'Created project {project.id} with {len(tasks)} tasks, 2 logs, {len(issues)} issues.')


if __name__ == '__main__':
    asyncio.run(seed_ship_repair_demo())
