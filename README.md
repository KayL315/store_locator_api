# Store Locator API

## 📌 Project Overview
This project is a production-ready Store Locator API built with FastAPI.  
It supports public store search functionality and secure internal store management with role-based access control (RBAC).

---

## 🚀 Tech Stack

- Backend: FastAPI
- Database: PostgreSQL (via SQLModel)
- Authentication: JWT (Access + Refresh Token)
- Caching: In-memory cache
- Geocoding: Nominatim API
- Testing: pytest
- Deployment: (fill later: Render / Railway)

---
## 🌐 Live Demo

https://store-locator-api-wv3e.onrender.com/docs

## Deployment

Live Demo:
https://store-locator-api-wv3e.onrender.com/docs

The application is deployed on Render with PostgreSQL.

## Docker

```bash
docker build -t store-locator .
docker run -p 10000:10000 \
  -e DATABASE_URL="postgresql://postgres:password@host.docker.internal:5432/store_locator" \
  -e JWT_SECRET="your-secret" \
  store-locator
  
## ⚙️ Features

### 1. Public Store Search API

- Search by:
  - Latitude & Longitude
  - Address (via geocoding)
  - Postal Code

- Filters:
  - radius_miles
  - services (AND logic)
  - store_types (OR logic)
  - open_now

- Distance Calculation:
  - Bounding Box + Haversine (geopy)

- Rate Limiting:
  - 10 requests / minute
  - 100 requests / hour

- Caching:
  - Geocoding results cached (30 days)

---

### 2. Authentication & Authorization

- JWT-based authentication:
  - Access Token (15 min)
  - Refresh Token (7 days)

- Role-Based Access Control:
  - Admin
  - Marketer
  - Viewer

---

### 3. Store Management (Admin / Marketer)

- Create store
- List stores (pagination)
- Get store details
- Update store (PATCH)
- Soft delete store

---

### 4. CSV Import (Upsert)

- Upload CSV file
- Create or update stores
- Validate:
  - headers
  - data format
  - coordinates
  - phone format
  - operating hours
- Transaction:
  - All-or-nothing rollback
- Response includes:
  - created count
  - updated count
  - failed rows

---

### 5. User Management (Admin Only)

- Create user
- List users
- Update user role/status
- Deactivate user

---

## 📦 Setup Instructions

### 1. Clone project

```bash
git clone https://github.com/KayL315/store_locator_api.git
cd store_locator_project