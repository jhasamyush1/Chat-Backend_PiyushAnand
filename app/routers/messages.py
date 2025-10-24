from fastapi import APIRouter, Depends, HTTPException, Query
from firebase_admin import db
from app.deps.auth import get_current_user
from app.models.schemas import SendMessage, MessageOut
import time, uuid
from app.ws.manager import ws_manager_broadcast

router = APIRouter(prefix="/rooms", tags=["messages"])

def assert_room_exists(room_id: str):
    if not db.reference(f"rooms/{room_id}").get():
        raise HTTPException(status_code=404, detail="Room not found")

import time, uuid
from fastapi import APIRouter, Depends
# from wherever you defined it:
from app.ws.manager import ws_manager_broadcast

router = APIRouter()

@router.post("/{room_id}/messages", response_model=MessageOut)
async def send_message(room_id: str, payload: SendMessage, user=Depends(get_current_user)):
    # 1) persist the message (your existing DB code)
    now_ms = int(time.time() * 1000)
    message_id = uuid.uuid4().hex
    data = {
        "sender_id": user["uid"],
        "text": payload.text,
        "created_at": now_ms,
        "read_by": {user["uid"]: True},
    }
    db.reference(f"rooms/{room_id}/messages/{message_id}").set(data)

    # 2) IMPORTANT: await the broadcast (this runs on the server loop)
    await ws_manager_broadcast(room_id, {
        "type": "message",
        "message_id": message_id,
        **data
    })

    # 3) return response
    return {"message_id": message_id, **data}

# typing function



@router.get("/{room_id}/messages", response_model=list[MessageOut])
def list_messages(
    room_id: str,
    user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    before: int | None = Query(None, description="Return messages with created_at < before (ms)"),
):
    assert_room_exists(room_id)
    snap = db.reference(f"rooms/{room_id}/messages").get() or {}
    msgs = []
    for mid, m in snap.items():
        if before is not None and m.get("created_at", 0) >= before:
            continue
        msgs.append({
            "message_id": mid,
            "sender_id": m.get("sender_id",""),
            "text": m.get("text",""),
            "created_at": m.get("created_at",0),
            "read_by": m.get("read_by", {}),
        })
    msgs.sort(key=lambda x: x["created_at"], reverse=True)
    return msgs[:limit]
