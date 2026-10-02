import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from main import app
import src.database as database


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(database, "engine", engine)
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def register(client, username, email):
    return client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "ClaveSegura123"},
    )


def token(client, username):
    response = client.post(
        "/auth/token", data={"username": username, "password": "ClaveSegura123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
