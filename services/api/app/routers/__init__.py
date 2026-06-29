"""API Routers"""
from app.routers import health, auth, customer, order, product, contract, procurement, inventory, tracking, settlement, file, user, notification, workflow, dashboard, integration, ai_agent, analytics, ship_repair

__all__ = [
    "health", "auth", "customer", "order", "product",
    "contract", "procurement", "inventory", "tracking",
    "settlement", "file", "user", "notification",
    "workflow", "dashboard", "integration", "ai_agent",
    "analytics", "ship_repair",
]
