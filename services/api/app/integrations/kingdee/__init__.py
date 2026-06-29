"""Kingdee Jingdouyun (金蝶精斗云) integration"""
from app.integrations.kingdee.client import KingdeeClient
from app.integrations.kingdee.sync_service import KingdeeSyncService

__all__ = ["KingdeeClient", "KingdeeSyncService"]
