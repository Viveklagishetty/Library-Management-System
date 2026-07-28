import importlib
import os
import tempfile
import uuid

import pytest


@pytest.fixture
def client():
    tmp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db").name
    old_db_file = os.environ.get("DB_FILE")
    os.environ["DB_FILE"] = tmp_db

    import app

    importlib.reload(app)
    test_client = app.app.test_client()

    yield test_client

    if old_db_file is None:
        os.environ.pop("DB_FILE", None)
    else:
        os.environ["DB_FILE"] = old_db_file

    if os.path.exists(tmp_db):
        os.remove(tmp_db)


def test_register_login_logout_flow(client):
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"

    register_response = client.post(
        "/register",
        data={"username": username, "email": email, "password": "secret123", "role": "member"},
        follow_redirects=True,
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/login",
        data={"username": username, "password": "secret123"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"/dashboard" in login_response.request.path.encode("utf-8") or b"dashboard" in login_response.data

    logout_response = client.get("/logout", follow_redirects=True)
    assert logout_response.status_code == 200
    assert b"/login" in logout_response.request.path.encode("utf-8") or b"login" in logout_response.data
