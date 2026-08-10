from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.reports import router as reports_router
from app.routers.risks import router as risks_router
from app.routers.brokerage import router as brokerage_router
from app.routers.spare_parts import router as spare_parts_router
from app.routers.quick_saves import router as quick_saves_router
from app.routers.knowledge import router as knowledge_router
from app.routers.customers import router as customers_router
from app.routers.files import router as files_router


def get_routers() -> list[tuple]:
    return [
        (auth_router, "/api/v1/auth", "认证"),
        (users_router, "/api/v1/users", "用户"),
        (projects_router, "/api/v1/projects", "项目"),
        (tasks_router, "/api/v1/tasks", "任务"),
        (reports_router, "/api/v1/reports", "报告"),
        (risks_router, "/api/v1/risks", "风险"),
        (brokerage_router, "/api/v1/brokerage", "经纪"),
        (spare_parts_router, "/api/v1/spare-parts", "备件"),
        (quick_saves_router, "/api/v1/quick-saves", "随手存"),
        (knowledge_router, "/api/v1/knowledge", "知识库"),
        (customers_router, "/api/v1/customers", "客户"),
        (files_router, "/api/v1/files", "文件"),
    ]


__all__ = [
    "auth_router",
    "users_router",
    "projects_router",
    "tasks_router",
    "reports_router",
    "risks_router",
    "brokerage_router",
    "spare_parts_router",
    "quick_saves_router",
    "knowledge_router",
    "customers_router",
    "files_router",
    "get_routers",
]