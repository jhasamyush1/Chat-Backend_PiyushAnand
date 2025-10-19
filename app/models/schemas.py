from pydantic import BaseModel, Field
from typing import Optional, Dict

class CreateRoom(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class RoomOut(BaseModel):
    room_id: str
    name: str
    created_by: str
    created_at: int

class SendMessage(BaseModel):
    text: str = Field(min_length=1, max_length=5000)

class MessageOut(BaseModel):
    message_id: str
    sender_id: str
    text: str
    created_at: int
    read_by: Optional[Dict[str, bool]] = None
