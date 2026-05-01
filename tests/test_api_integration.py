import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -------------------------
# 1. LOGIN TEST
# -------------------------
def test_login_success():
    response = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "TestPassword123!"
    })

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


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
    login = client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "TestPassword123!"
    })

    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/admin/stores", json={
        "store_id": "TEST2",
        "name": "Test Store 2",
        "store_type": "regular",
        "status": "active",
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