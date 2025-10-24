# app/ws/manager.py
from typing import Dict, Set, List
from starlette.websockets import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

_rooms: Dict[str, Set[WebSocket]] = {}

def _room(room_id: str) -> Set[WebSocket]:
    return _rooms.setdefault(room_id, set())

async def ws_manager_join(room_id: str, ws: WebSocket) -> None:
    _room(room_id).add(ws)

def ws_manager_leave(room_id: str, ws: WebSocket) -> None:
    if room_id in _rooms:
        _rooms[room_id].discard(ws)
        if not _rooms[room_id]:
            _rooms.pop(room_id, None)

# async def ws_manager_broadcast(room_id: str, payload: dict) -> None:
#     """
#     Broadcast to all sockets in room. This MUST be awaited from an async context.
#     """
#     text = json.dumps(payload)
#     conns: List[WebSocket] = list(_rooms.get(room_id, set()))
#     if not conns:
#         return
    

#     # --- ADD BELOW: broadcast to everyone EXCEPT one websocket (the sender) ---
# async def ws_manager_broadcast_except(room_id: str, payload: dict, exclude: WebSocket | None) -> None:
#     """
#     Broadcast payload to all sockets in the room EXCEPT the `exclude` websocket.
#     Safe: awaits sends and ignores broken sockets.
#     """
#     text = json.dumps(payload)
#     conns = [ws for ws in list(_rooms.get(room_id, set())) if ws is not exclude]
#     if not conns:
#         return

#     results = await asyncio.gather(*(ws.send_text(text) for ws in conns), return_exceptions=True)

#     # Drop dead sockets (same policy as your broadcast)
#     for ws, res in zip(conns, results):
#         if isinstance(res, Exception):
#             logging.getLogger(__name__).warning("WS send failed in broadcast_except; dropping socket: %r", res)
#             ws_manager_leave(room_id, ws)
# --- END ADD ---

async def ws_manager_broadcast(room_id: str, payload: dict) -> None:
    """
    Broadcast to all sockets in the given room.
    This MUST be awaited from an async context.
    """
    text = json.dumps(payload)
    conns: List[WebSocket] = list(_rooms.get(room_id, set()))
    if not conns:
        return

    # Send to all concurrently, but AWAIT completion so errors are not lost.
    results = await asyncio.gather(
        *(ws.send_text(text) for ws in conns),
        return_exceptions=True
    )

    # Remove dead/broken sockets
    for ws, res in zip(conns, results):
        if isinstance(res, Exception):
            logger.warning("WS send failed; dropping socket: %r", res)
            ws_manager_leave(room_id, ws)


async def ws_manager_broadcast_except(room_id: str, payload: dict, exclude: WebSocket | None) -> None:
    """
    Broadcast payload to all sockets in the room EXCEPT the `exclude` websocket.
    Safe: awaits sends and ignores broken sockets.
    """
    text = json.dumps(payload)
    conns = [ws for ws in list(_rooms.get(room_id, set())) if ws is not exclude]
    if not conns:
        return

    results = await asyncio.gather(*(ws.send_text(text) for ws in conns), return_exceptions=True)

    # Drop dead sockets (same policy as your broadcast)
    for ws, res in zip(conns, results):
        if isinstance(res, Exception):
            logging.getLogger(__name__).warning("WS send failed in broadcast_except; dropping socket: %r", res)
            ws_manager_leave(room_id, ws)




    # Send to all concurrently, but AWAIT completion so errors are not lost.
    results = await asyncio.gather(
        *(ws.send_text(text) for ws in conns),
        return_exceptions=True
    )

    # Remove dead/broken sockets
    for ws, res in zip(conns, results):
        if isinstance(res, Exception):
            logger.warning("WS send failed; dropping socket: %r", res)
            ws_manager_leave(room_id, ws)
