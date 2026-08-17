"""实时推送（WebSocket）。

- 单进程内连接管理（ConnectionManager），按 project_id 分房间。
- 鉴权：客户端通过 query 参数 `?token=<JWT>` 传递访问令牌（浏览器 WS 无法自定义头）。
- 业务侧通过 `manager.broadcast(project_id, message)` 向某项目的在线连接广播事件。
  注意：当前为单 worker 部署（见 Dockerfile），广播仅在本进程内生效；
  若扩展到多 worker 需引入 Redis pub/sub，本模块接口保持不变。
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.security import verify_access_token

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        # project_id -> 该项目的活动 WebSocket 连接集合
        self.rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, project_id: int, ws: WebSocket) -> None:
        self.rooms.setdefault(project_id, set()).add(ws)

    def disconnect(self, project_id: int, ws: WebSocket) -> None:
        room = self.rooms.get(project_id)
        if room:
            room.discard(ws)
            if not room:
                self.rooms.pop(project_id, None)

    async def broadcast(self, project_id: int, message: dict) -> None:
        for ws in list(self.rooms.get(project_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(project_id, ws)


manager = ConnectionManager()


async def _authenticate(token: str | None) -> int | None:
    if not token:
        return None
    try:
        payload = verify_access_token(token)
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None


@router.websocket("/ws/projects/{project_id}")
async def ws_project_room(
    websocket: WebSocket,
    project_id: int,
    token: str | None = Query(default=None),
) -> None:
    user_id = await _authenticate(token)
    if user_id is None:
        # 未授权：以 4401 关闭（类 HTTP 401）
        await websocket.close(code=4401)
        return

    await websocket.accept()
    await manager.connect(project_id, websocket)
    try:
        # 保持连接；仅消费客户端消息以探测断开，业务事件由服务端主动推送。
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
    except Exception:
        manager.disconnect(project_id, websocket)
