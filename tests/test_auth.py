import pytest
from httpx import AsyncClient, ASGITransport
from ratemate_app.main import app

async def register(ac: AsyncClient, username: str, email: str, password: str):
    resp = await ac.post("/auth/register", json={"username": username, "email": email, "password": password})
    return resp.status_code, resp.json()

async def login(ac: AsyncClient, username: str, password: str):
    resp = await ac.post("/auth/login", json={"username": username, "password": password})
    return resp.status_code, resp.json()

async def delete_me(ac: AsyncClient, token: str):
    resp = await ac.delete("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return resp.status_code

@pytest.mark.asyncio
async def test_register_user_success_and_cleanup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        status, data = await register(ac, "user_t1", "user_t1@example.com", "secret")
        assert status == 201
        
        assert "access_token" in data and data["token_type"] == "bearer"
        del_status = await delete_me(ac, data["access_token"])
        assert del_status == 204

@pytest.mark.asyncio
async def test_register_duplicate_username_and_cleanup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        status1, data1 = await register(ac, "user_dup", "user_dup@example.com", "secret")
        assert status1 == 201

        status2, _ = await register(ac, "user_dup", "other@example.com", "secret")
        assert status2 == 400

        del_status = await delete_me(ac, data1["access_token"])
        assert del_status == 204

@pytest.mark.asyncio
async def test_login_success_and_cleanup():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        status_reg, data_reg = await register(ac, "user_login", "user_login@example.com", "secret")
        assert status_reg == 201

        status_log, data_log = await login(ac, "user_login", "secret")
        assert status_log == 200

        assert "access_token" in data_log and data_log["token_type"] == "bearer"
        del_status = await delete_me(ac, data_log["access_token"])
        assert del_status == 204

@pytest.mark.asyncio
async def test_delete_me_then_login_fails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        status_reg, data_reg = await register(ac, "user_del", "user_del@example.com", "secret")
        assert status_reg == 201

        del_status = await delete_me(ac, data_reg["access_token"])
        assert del_status == 204

        status_log, _ = await login(ac, "user_del", "secret")
        assert status_log == 401