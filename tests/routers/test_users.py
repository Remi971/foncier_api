from __future__ import annotations
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

#ARRANGE
@pytest.fixture
def user():
    return {
        "username":"test@yopmail.com",
        "password":'test'
    }

#ACT
@pytest.fixture
def token(user):
    response = client.post(
        '/token',
        data=user
    )
    new_token = response.json().get("access_token")
    return new_token
    
def test_users_get_all(token):
    response = client.get(
        '/users/',
        headers={"Authorization": f"bearer {token}"}
    )
    assert response.status_code == 200