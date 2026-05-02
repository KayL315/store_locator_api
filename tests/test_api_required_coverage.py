from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select
from rate_limit import rate_limiter
from main import app
from database import engine
from models import User, RefreshToken
from auth import hash_password
from seed_users import seed_users

client = TestClient(app)


def reset_user(email: str, password: str = "TestPassword123!"):
    seed_users()

    with Session(engine) as db:
        user = db.exec(select(User).where(User.email == email)).first()
        assert user is not None

        user.hashed_password = hash_password(password)
        user.must_change_password = False
        user.status = "active"

        old_tokens = db.exec(
            select(RefreshToken).where(RefreshToken.user_id == user.user_id)
        ).all()
        for token in old_tokens:
            db.delete(token)

        db.add(user)
        db.commit()


def login(email: str, password: str = "TestPassword123!") -> dict:
    reset_user(email, password)

    response = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })

    assert response.status_code == 200
    return response.json()


def test_search_by_postal_code_with_mock_geocoding():
    rate_limiter.requests.clear()
    with patch("main.geocode_address") as mock_geocode:
        mock_geocode.return_value = {"lat": 42.3601, "lon": -71.0589}

        response = client.post("/api/stores/search", json={
            "postal_code": "02114",
            "radius_miles": 10,
        })

    assert response.status_code == 200
    assert "stores" in response.json()
    assert "metadata" in response.json()


def test_search_filters_services_and_store_types():
    rate_limiter.requests.clear()
    response = client.post("/api/stores/search", json={
        "lat": 42.3601,
        "lon": -71.0589,
        "radius_miles": 20,
        "services": ["pickup"],
        "store_types": ["regular", "flagship"],
        "open_now": False,
    })

    assert response.status_code == 200
    data = response.json()
    assert "stores" in data
    assert "metadata" in data


def test_refresh_and_logout_flow():
    tokens = login("admin@test.com")
    refresh_token = tokens["refresh_token"]

    refresh_response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

    logout_response = client.post("/api/auth/logout", json={
        "refresh_token": refresh_token
    })

    assert logout_response.status_code == 200

    refresh_after_logout = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert refresh_after_logout.status_code == 401


def test_viewer_cannot_create_store():
    tokens = login("viewer@test.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = client.post("/api/admin/stores", json={
        "store_id": f"VIEWER-{uuid4().hex[:8]}",
        "name": "Viewer Store",
        "store_type": "regular",
        "status": "active",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "address_street": "100 Main St",
        "address_city": "Boston",
        "address_state": "MA",
        "address_postal_code": "02114",
        "address_country": "USA",
        "phone": "617-555-1234",
        "services": ["pickup"],
        "operating_hours": {"mon": "08:00-22:00"},
    }, headers=headers)

    assert response.status_code == 403


def test_marketer_cannot_manage_users():
    tokens = login("marketer@test.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = client.get("/api/admin/users", headers=headers)

    assert response.status_code == 403