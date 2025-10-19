from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import db
from app.deps.auth import get_current_user
from app.models.schemas import CreateRoom, RoomOut
import time, uuid

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", response_model=RoomOut)
def create_room(payload: CreateRoom, user=Depends(get_current_user)):
    room_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    data = {"name": payload.name, "created_by": user["uid"], "created_at": now_ms}
    db.reference(f"rooms/{room_id}").set(data)
    return {"room_id": room_id, **data}

@router.get("", response_model=list[RoomOut])
def list_rooms(user=Depends(get_current_user)):
    snap = db.reference("rooms").get() or {}
    out = [{
        "room_id": rid,
        "name": r.get("name",""),
        "created_by": r.get("created_by",""),
        "created_at": r.get("created_at",0),
    } for rid, r in snap.items()]
    out.sort(key=lambda x: x["created_at"], reverse=True)
    return out
