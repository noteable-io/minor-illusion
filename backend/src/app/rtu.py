import uuid
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.auth import get_user
from app.schemas import UserOut

# NOTE: Websockets attached to an APIRouter with a prefix
# will fail and always return 403.
# See https://github.com/tiangolo/fastapi/issues/98
# For now, skip prefix and just make sure to include
# /rtu in the appropriate paths

router = APIRouter(tags=["rtu"])


class RTUData(BaseModel):
    class Config:
        extra = "allow"


class RTURequest(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event: str
    data: Optional[RTUData]

    class Config:
        json_encoders = {uuid.UUID: lambda v: str(v)}


class RTUReply(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    req_id: uuid.UUID
    data: Optional[RTUData]

    class Config:
        json_encoders = {uuid.UUID: lambda v: str(v)}


class WebsocketSession:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.n_read = 0
        self.n_written = 0
        self.user = None

    async def auth_user(self, token: str):
        self.user = await get_user(token)
        return UserOut.from_orm(self.user).dict()

    async def session_stats(self):
        return {
            "n_read": self.n_read,
            "n_written": self.n_written,
            "user": self.user.name if self.user else "Not authenticated",
        }

    async def process(self, message: dict):
        req = RTURequest(**message)
        if req.event == "auth":
            data = await self.auth_user(req.data.token)
            response = RTUReply(req_id=req.id, data=RTUData(**data))
        elif req.event == "session_stats":
            data = await self.session_stats()
            response = RTUReply(req_id=req.id, data=RTUData(**data))
        return response

    async def listen(self):
        while True:
            try:
                message = await self.websocket.receive_json()
                self.n_read += 1
                response = await self.process(message)
                await self.websocket.send_text(response.json())
                self.n_written += 1
            except WebSocketDisconnect:
                break

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@router.websocket("/rtu")
async def rtu(websocket: WebSocket):
    await websocket.accept()
    async with WebsocketSession(websocket) as session:
        await session.listen()
