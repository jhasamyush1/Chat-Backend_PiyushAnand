""" from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from firebase_admin import auth as admin_auth, db
from app.ws.manager import (
    ws_manager_join,
    ws_manager_leave,
    ws_manager_broadcast_except,   # <-- ADD THIS
)

import json


router = APIRouter(tags=["ws"])


def verify_token_or_401(token: str):
    try:
        decoded = admin_auth.verify_id_token(token)
        return {"uid": decoded.get("uid"), "email": decoded.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def assert_room_exists(room_id: str):
    if not db.reference(f"rooms/{room_id}").get():
        raise HTTPException(status_code=404, detail="Room not found")


@router.websocket("/ws/rooms/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str, token: str = Query(...)):
    user = verify_token_or_401(token)
    assert_room_exists(room_id)
    await websocket.accept()
    await ws_manager_join(room_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_text(json.dumps({"type": "noop"}))
                continue

            if msg.get("type") == "typing":
                db.reference(f"rooms/{room_id}/typing/{user['uid']}").set(bool(msg.get("value")))
                await websocket.send_text(
                    json.dumps({"type": "typing_ack", "value": bool(msg.get("value"))})
                )

            elif msg.get("type") == "read_upto":
                upto = int(msg.get("created_at_ms", 0))
                all_msgs = db.reference(f"rooms/{room_id}/messages").get() or {}
                for mid, m in all_msgs.items():
                    if m.get("created_at", 0) <= upto:
                        db.reference(f"rooms/{room_id}/messages/{mid}/read_by/{user['uid']}").set(True)
                await websocket.send_text(json.dumps({"type": "read_ack", "upto": upto}))

            else:
                await websocket.send_text(json.dumps({"type": "noop"}))

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager_leave(room_id, websocket)
 """



from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from firebase_admin import auth as admin_auth, db
from app.ws.manager import (
    ws_manager_join,
    ws_manager_leave,
    ws_manager_broadcast_except,   # <-- used for typing broadcast
)

import json


router = APIRouter(tags=["ws"])


def verify_token_or_401(token: str):
    try:
        decoded = admin_auth.verify_id_token(token)
        return {"uid": decoded.get("uid"), "email": decoded.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def assert_room_exists(room_id: str):
    if not db.reference(f"rooms/{room_id}").get():
        raise HTTPException(status_code=404, detail="Room not found")


@router.websocket("/ws/rooms/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str, token: str = Query(...)):
    user = verify_token_or_401(token)
    assert_room_exists(room_id)
    await websocket.accept()
    await ws_manager_join(room_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_text(json.dumps({"type": "noop"}))
                continue

            if msg.get("type") == "typing":
                # normalize value
                is_typing = bool(msg.get("value"))

                # update typing state in DB (kept from your original code)
                db.reference(f"rooms/{room_id}/typing/{user['uid']}").set(is_typing)

                # notify everyone else in the room (not the sender)
                await ws_manager_broadcast_except(
                    room_id,
                    {"type": "typing", "user_id": user["uid"], "value": is_typing},
                    exclude=websocket,
                )

                # ACK back to the sender (kept behavior)
                await websocket.send_text(json.dumps({"type": "typing_ack", "value": is_typing}))

            elif msg.get("type") == "read_upto":
                upto = int(msg.get("created_at_ms", 0))
                all_msgs = db.reference(f"rooms/{room_id}/messages").get() or {}
                for mid, m in all_msgs.items():
                    if m.get("created_at", 0) <= upto:
                        db.reference(f"rooms/{room_id}/messages/{mid}/read_by/{user['uid']}").set(True)
                await websocket.send_text(json.dumps({"type": "read_ack", "upto": upto}))

            else:
                await websocket.send_text(json.dumps({"type": "noop"}))

    except WebSocketDisconnect:
        # Clear typing on disconnect and inform others
        try:
            db.reference(f"rooms/{room_id}/typing/{user['uid']}").set(False)
        except Exception:
            pass
        await ws_manager_broadcast_except(
            room_id,
            {"type": "typing", "user_id": user["uid"], "value": False},
            exclude=websocket,
        )
    finally:
        ws_manager_leave(room_id, websocket)
