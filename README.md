# 🏪 Store Locator API

## 📌 Project Description

A production-ready Store Locator API built with FastAPI, supporting geospatial search, authentication, RBAC, CSV import, and scalable backend design.

---

## 🌐 Live Demo

https://store-locator-api-wv3e.onrender.com/docs

---


## 📂 GitHub Repository

https://github.com/KayL315/store_locator_api
---


## 🚀 Tech Stack

- Backend: FastAPI
- Database: PostgreSQL (SQLModel)
- Auth: JWT (Access + Refresh Tokens)
- Cache: In-memory TTL
- Geocoding: Nominatim API
- Testing: pytest
- Deployment: Render + Docker

---

## 🏗 Architecture Overview

Client → FastAPI → Business Logic → PostgreSQL → Cache

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

### Authentication
POST /api/auth/login  
POST /api/auth/refresh  
POST /api/auth/logout  

### Store Management
POST /api/admin/stores  
GET /api/admin/stores  
PATCH /api/admin/stores/{id}  
DELETE /api/admin/stores/{id}

### CSV Import
POST /api/admin/stores/import

---

## 📄 CSV Processing Choice

Uses Python built-in csv module.

---

## 🔐 Authentication Flow

1. Change password if first login  
2. Login → get tokens  
3. Use Bearer token  
4. Refresh token when expired  
5. Logout to revoke  

---

## 📏 Distance Calculation

Haversine formula.

---

## 🧪 Testing

Run:

pytest

Coverage:

pytest --cov=. --cov-report=term-missing

Coverage ≥ 60%

---

## 🗄 Database Setup

alembic upgrade head  
python create_indexes.py  
python seed_users.py  

---

## ▶️ Run Locally

uvicorn main:app --reload

---
## 🔄 CI/CD

This project uses GitHub Actions for Continuous Integration.

### Pipeline includes:
- Install dependencies
- Run test suite
- Generate coverage report
- Fail build if tests fail

### Trigger:
- On push to `main`
- On pull request

This ensures code quality and prevents breaking changes.

---

## 🐳 Docker

The application is containerized using Docker.

### Build:
docker build -t store-locator .

### Run:
docker run -p 10000:10000 store-locator

### Benefits:
- Environment consistency
- Easy deployment
- Scalable infrastructure
---

## 🔑 Test Credentials

Admin: admin@test.com / TestPassword123!  
Marketer: marketer@test.com / TestPassword123!  
Viewer: viewer@test.com / TestPassword123!  

---

## 📡 API Docs

https://store-locator-api-wv3e.onrender.com/docs

---

## 🚀 Deployment

Platform: Render  
URL: https://store-locator-api-wv3e.onrender.com  

---
## 🧩 Project Management

This project was organized using Jira.
Jira board:
https://kaymengyaoliu.atlassian.net/jira/software/projects/SL/boards/2?atlOrigin=eyJpIjoiYmNlYzdkYmJjOTljNDQ3Zjg1NjhhYThkMTM0YmNmNzIiLCJwIjoiaiJ9

### Used for:
- Task tracking
- Feature breakdown
- Sprint planning

### Example tasks:
- Implement authentication system
- Add RBAC permissions
- Build geospatial search
- Implement CSV import
- Add caching layer

This helped structure development and track progress.
---

## 🧾 Health Check

GET /api/health

---

## 🎯 Summary

Production-level backend with search, auth, RBAC, caching, testing, and deployment.
