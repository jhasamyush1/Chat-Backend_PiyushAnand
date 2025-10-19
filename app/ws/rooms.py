from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from firebase_admin import auth as admin_auth, db
from app.ws.manager import ws_manager_join, ws_manager_leave
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
