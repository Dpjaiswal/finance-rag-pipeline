from app.schemas.auth import DEFAULT_COMPANY_NAME
from tests.conftest import auth_header


def test_register_and_login(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "New User",
            "email": "new@example.com",
            "password": "Password123!",
            "company_name": "Acme Finance",
        },
    )
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": "Password123!"})
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_unversioned_register_accepts_name_field(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Akash",
            "email": "akash@gmail.com",
            "password": "password",
            "company_name": "google",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["full_name"] == "Akash"


def test_register_matches_basic_spec_without_company_name(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Basic User",
            "email": "basic@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["company_name"] == DEFAULT_COMPANY_NAME


def test_admin_assigns_role(client):
    headers = auth_header(client, "admin@example.com", "Admin123!")
    response = client.post("/api/v1/users/assign-role", json={"user_id": 3, "role_name": "Financial Analyst"}, headers=headers)
    assert response.status_code == 200
    assert "Financial Analyst" in response.json()["roles"]


def test_client_cannot_assign_role(client):
    headers = auth_header(client, "client@example.com", "Client123!")
    response = client.post("/api/v1/users/assign-role", json={"user_id": 3, "role_name": "Admin"}, headers=headers)
    assert response.status_code == 403
