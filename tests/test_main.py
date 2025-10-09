from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    
def test_login():
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"},
    )
    assert response.status_code == 404  # Assuming the user does not exist yet

def test_signin():
    response = client.post(
        "/signin",
        json={
            "email": "test@yopmail.com", 
            "password": "test", 
            "firstname": "John Snow",
            "lastname": "Snow",
            },
    )
    assert response.status_code == 400
    
