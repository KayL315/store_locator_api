# 🏪 Store Locator API

## 📌 Overview

A production-ready Store Locator API built with FastAPI.

This system supports:
- High-performance geospatial store search
- Secure internal store management
- Role-Based Access Control (RBAC)
- CSV batch import with validation and upsert
- Scalable architecture with caching and indexing

---

## 🌐 Live Demo

https://store-locator-api-wv3e.onrender.com/docs

---

## 🚀 Tech Stack

- Backend: FastAPI
- Database: PostgreSQL (SQLModel / SQLAlchemy)
- Authentication: JWT (Access + Refresh Tokens)
- Caching: In-memory cache (TTL-based)
- Geocoding: Nominatim API
- Testing: pytest (Unit + Integration)
- Deployment: Render + Docker

---

## 🏗 Architecture Overview

Client → FastAPI → Service Layer → PostgreSQL → Cache

---

## 🔍 Key Design Decisions

### Geospatial Search
Bounding Box → Haversine → Sort

### Caching
- Geocoding: 30 days
- Search: 5 minutes

### RBAC
User → Role → Permissions

### Rate Limiting
- 10/min
- 100/hour

---

## ⚙️ Features

### Store Search
POST /api/stores/search

Supports:
- Lat/Lon
- Address
- Postal Code

### Auth
POST /api/auth/login

### Store Management
POST /api/admin/stores  
GET /api/admin/stores  
PATCH /api/admin/stores/{id}  
DELETE /api/admin/stores/{id}

### CSV Import
POST /api/admin/stores/import

## CSV Processing Choice

This project uses Python's built-in `csv` module for the API CSV import endpoint.

## Test Credentials

Admin:
- Email: admin@test.com
- Default Password: TestPassword123!
- First login requires password change.

Marketer:
- Email: marketer@test.com
- Default Password: TestPassword123!

Viewer:
- Email: viewer@test.com
- Default Password: TestPassword123!

## Authentication Flow

1. Call `/api/auth/change-password` if using a seed user's default password.
2. Call `/api/auth/login` to receive access and refresh tokens.
3. Click Authorize in Swagger and use: `Bearer <access_token>`.
4. Use `/api/auth/refresh` to get a new access token.
5. Use `/api/auth/logout` to revoke the refresh token.

## Run Database Migrations

```bash
alembic upgrade head
python create_indexes.py
python seed_users.py
---

## 🧪 Testing

pytest

---

## 🐳 Docker

docker build -t store-locator .
docker run -p 10000:10000 store-locator

---

## 📦 Setup

git clone https://github.com/KayL315/store_locator_api.git
cd store_locator_project
pip install -r requirements.txt
uvicorn main:app --reload

---

## 🎯 Summary

Production-level backend system with search, auth, RBAC, caching, and testing.
