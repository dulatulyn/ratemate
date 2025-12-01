import os, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import AsyncClient, ASGITransport
from ratemate_app.main import app
from ratemate_app.db.session import init_db

async def register(ac: AsyncClient, username: str, email: str, password: str):
    resp = await ac.post("/auth/register", json={"username": username, "email": email, "password": password})
    return resp.status_code, resp.json()

async def login(ac: AsyncClient, username: str, password: str):
    resp = await ac.post("/auth/login", json={"username": username, "password": password})
    return resp.status_code, resp.json()

async def delete_me(ac: AsyncClient, token: str):
    resp = await ac.delete("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return resp.status_code

async def create_post_api(ac: AsyncClient, token: str, title: str, content: str):
    resp = await ac.post("/posts/", json={"title": title, "content": content}, headers={"Authorization": f"Bearer {token}"})
    return resp.status_code, resp.json()

async def create_comment_api(ac: AsyncClient, token: str, post_id: int, content: str, parent_id: int | None = None):
    payload = {"post_id": post_id, "content": content}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    resp = await ac.post("/comments/", json=payload, headers={"Authorization": f"Bearer {token}"})
    return resp.status_code, resp.json()

async def rate_comment_api(ac: AsyncClient, token: str, comment_id: int, score: int):
    resp = await ac.post(f"/comments/{comment_id}/rate", json={"score": score}, headers={"Authorization": f"Bearer {token}"})
    return resp.status_code, resp.json()

async def rate_post_api(ac: AsyncClient, token: str, post_id: int, score: int):
    resp = await ac.post(f"/posts/{post_id}/rate", json={"score": score}, headers={"Authorization": f"Bearer {token}"})
    return resp.status_code, resp.json()

async def delete_comment_api(ac: AsyncClient, token: str, comment_id: int):
    resp = await ac.delete(f"/comments/{comment_id}", headers={"Authorization": f"Bearer {token}"})
    return resp.status_code

async def delete_post_api(ac: AsyncClient, token: str, post_id: int):
    resp = await ac.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {token}"})
    return resp.status_code

@pytest.mark.asyncio
async def test_full_flow_user_post_comment_ratings_delete_cycle():
    
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        status_reg, data_reg = await register(ac, "flow_user", "flow_user@example.com", "secret")
        assert status_reg == 201

        status_log, data_log = await login(ac, "flow_user", "secret")
        assert status_log == 200
        token = data_log["access_token"]

        stp, post = await create_post_api(ac, token, "title", "post")
        assert stp == 201
        pid = post["id"]

        stc, comment = await create_comment_api(ac, token, pid, "comment")
        assert stc == 201
        cid = comment["id"]

        src, r1 = await rate_comment_api(ac, token, cid, 8)
        assert src == 201
        assert r1.get("success") is True

        srp, r2 = await rate_post_api(ac, token, pid, 9)
        assert srp == 201
        assert r2.get("success") is True

        dc = await delete_comment_api(ac, token, cid)
        assert dc == 204

        dp = await delete_post_api(ac, token, pid)
        assert dp == 204

        du = await delete_me(ac, token)
        assert du == 204


# @pytest.mark.asyncio
# async def test_register_user_success_and_cleanup():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         status, data = await register(ac, "user_t1", "user_t1@example.com", "secret")
#         assert status == 201
        
#         assert "access_token" in data and data["token_type"] == "bearer"
#         del_status = await delete_me(ac, data["access_token"])
#         assert del_status == 204

# @pytest.mark.asyncio
# async def test_register_duplicate_username_and_cleanup():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         status1, data1 = await register(ac, "user_dup", "user_dup@example.com", "secret")
#         assert status1 == 201
        
#         status2, _ = await register(ac, "user_dup", "other@example.com", "secret")
#         assert status2 == 400

#         del_status = await delete_me(ac, data1["access_token"])
#         assert del_status == 204

# @pytest.mark.asyncio
# async def test_login_success_and_cleanup():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         status_reg, data_reg = await register(ac, "user_login", "user_login@example.com", "secret")
#         assert status_reg == 201

#         status_log, data_log = await login(ac, "user_login", "secret")
#         assert status_log == 200

#         assert "access_token" in data_log and data_log["token_type"] == "bearer"
#         del_status = await delete_me(ac, data_log["access_token"])
#         assert del_status == 204

# @pytest.mark.asyncio
# async def test_delete_me_then_login_fails():
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         status_reg, data_reg = await register(ac, "user_del", "user_del@example.com", "secret")
#         assert status_reg == 201

#         del_status = await delete_me(ac, data_reg["access_token"])
#         assert del_status == 204

#         status_log, _ = await login(ac, "user_del", "secret")
#         assert status_log == 401