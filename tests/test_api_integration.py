import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


def change_admin_password():
    response = client.post("/api/auth/change-password", json={
        "email": "admin@test.com",
        "current_password": "TestPassword123!",
        "new_password": "NewPassword123!"
    })

    if response.status_code == 200:
        return

    response = client.post("/api/auth/change-password", json={
        "email": "admin@test.com",
        "current_password": "NewPassword123!",
        "new_password": "NewPassword123!"
    })

    assert response.status_code == 200


def login_admin():
    change_admin_password()

    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "NewPassword123!"
    })

    assert response.status_code == 200
    return response.json()["access_token"]
# -------------------------
# 1. LOGIN TEST
# -------------------------
def test_login_success():
    token = login_admin()

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

# -------------------------
# 2. SEARCH BY LAT/LON
# -------------------------
def test_search_by_coordinates():
    response = client.post("/api/stores/search", json={
        "lat": 42.3601,
        "lon": -71.0589,
        "radius_miles": 10
    })

    assert response.status_code == 200
    data = response.json()

    assert "stores" in data
    assert "metadata" in data


# -------------------------
# 3. SEARCH BY ADDRESS (geocode)
# -------------------------
def test_search_by_address():
    response = client.post("/api/stores/search", json={
        "address": "Boston, MA",
        "radius_miles": 10
    })

    assert response.status_code == 200
    data = response.json()

    assert "stores" in data


# -------------------------
# 4. RBAC TEST (Protected Endpoint)
# -------------------------
def test_create_store_requires_auth():
    response = client.post("/api/admin/stores", json={
        "store_id": "TEST1",
        "name": "Test Store",
        "store_type": "regular",
        "status": "active",
        "address_street": "Boston",
        "address_city": "Boston",
        "address_state": "MA",
        "address_postal_code": "02114",
        "address_country": "USA",
        "services": [],
        "operating_hours": {"mon": "08:00-22:00"}
    })

    assert response.status_code in (401, 403)


# -------------------------
# 5. CREATE STORE WITH AUTH
# -------------------------
def test_create_store_with_auth():
    token = login_admin()
    headers = {"Authorization": f"Bearer {token}"}

    store_id = f"TEST-{uuid4().hex[:8]}"

    response = client.post("/api/admin/stores", json={
        "store_id": store_id,
        "name": "Test Store 2",
        "store_type": "regular",
        "status": "active",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "address_street": "Boston",
        "address_city": "Boston",
        "address_state": "MA",
        "address_postal_code": "02114",
        "address_country": "USA",
        "services": [],
        "operating_hours": {"mon": "08:00-22:00"}
    }, headers=headers)

    assert response.status_code in (200, 201)

# -------------------------
# 6. RATE LIMIT TEST
# -------------------------
def test_rate_limit():
    for _ in range(11):
        response = client.post("/api/stores/search", json={
            "lat": 42.3601,
            "lon": -71.0589
        })

    assert response.status_code == 429