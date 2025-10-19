from typing import Dict, Set
from starlette.websockets import WebSocket
import asyncio, json

_rooms: Dict[str, Set[WebSocket]] = {}

def _get_room(room_id: str) -> Set[WebSocket]:
    return _rooms.setdefault(room_id, set())

async def ws_manager_join(room_id: str, ws: WebSocket):
    _get_room(room_id).add(ws)

def ws_manager_leave(room_id: str, ws: WebSocket):
    if room_id in _rooms:
        _rooms[room_id].discard(ws)
        if not _rooms[room_id]:
            _rooms.pop(room_id, None)

def ws_manager_broadcast(room_id: str, payload: dict):
    text = json.dumps(payload)
    for ws in list(_rooms.get(room_id, set())):
        try:
            asyncio.create_task(ws.send_text(text))
        except Exception:
            pass
