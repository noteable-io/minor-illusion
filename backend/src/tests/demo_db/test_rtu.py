from typing import AsyncContextManager, Callable

import pytest
from app.models import UserDAO
from app.rtu import RTUData, RTUReply, RTURequest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import WebSocketTestSession


@pytest.mark.asyncio
class TestRTU:
    @pytest.fixture(autouse=True)
    def patch_auth_file(
        self,
        mocker: MockerFixture,
        db_session: Callable[[], AsyncContextManager[AsyncSession]],
    ):
        mocker.patch("app.auth.db_session", db_session)

    async def test_rtu(self, ws_client: WebSocketTestSession):
        req = RTURequest(event="session_stats")
        ws_client.send_text(req.json())
        response_js = ws_client.receive_json()
        response = RTUReply(**response_js)
        assert response.req_id == req.id
        assert response.data.user == "Not authenticated"
        assert response.data.n_read == 1
        assert response.data.n_written == 0

    async def test_valid_login(
        self, ws_client: WebSocketTestSession, auth_token: str, fake_user: UserDAO
    ):

        req = RTURequest(event="auth", data=RTUData(token=auth_token))
        ws_client.send_text(req.json())
        response_js = ws_client.receive_json()
        response = RTUReply(**response_js)
        assert response.req_id == req.id
        assert response.data.id == fake_user.id
        assert response.data.name == fake_user.name
