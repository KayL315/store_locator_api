import csv
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from database import get_session, engine
from schemas import StoreSearchRequest, StoreSearchResponse, LoginRequest, TokenResponse, RefreshRequest, LogoutRequest, StoreCreate, StoreUpdate, UserCreate, UserUpdate, ChangePasswordRequest
from search_logic import search_nearby_stores
from geocoding import geocode_address
from rate_limit import rate_limit_dependency
from datetime import datetime, timedelta
from models import User, RefreshToken, Store, Role, Service
from auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
    require_permissions,
    hash_password,
    hash_token,
    get_current_user,
)
from csv_validation import validate_csv_headers, validate_store_row
from contextlib import asynccontextmanager
from seed_users import seed_users
from fastapi.middleware.cors import CORSMiddleware
from datetime import timezone

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🌱 Seeding users...")
    seed_users()

    yield

app = FastAPI(
    title="Store Locator API",
    description="Production-ready Store Locator API built with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)
#之后还可以把前端部署url放进来，这样就允许前端网页来调用后端api了
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://store-locator-api-wv3e.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_or_create_services(db: Session, service_names: list[str]) -> list[Service]:
    services = []

    for service_name in service_names:
        service = db.exec(
            select(Service).where(Service.name == service_name)
        ).first()

        if not service:
            service = Service(name=service_name)
            db.add(service)
            db.commit()
            db.refresh(service)

        services.append(service)

    return services

def build_full_address(
    address_street: str,
    address_city: str,
    address_state: str,
    address_postal_code: str,
    address_country: str,
) -> str:
    return (
        f"{address_street}, "
        f"{address_city}, "
        f"{address_state} "
        f"{address_postal_code}, "
        f"{address_country}"
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "message": "Store Locator Service is running",
    }


@app.post("/api/stores/search", response_model=StoreSearchResponse)
def search_stores(
    request: StoreSearchRequest,
    db: Session = Depends(get_session),
    _: None = Depends(rate_limit_dependency),
):
    
    lat = request.lat
    lon = request.lon
    if lat is None or lon is None:

        if request.address:

            geo = geocode_address(request.address)

        elif request.postal_code:

            geo = geocode_address(request.postal_code)

        else:

            raise HTTPException(status_code=400, detail="No valid location input")

        if not geo:

            raise HTTPException(status_code=400, detail="Geocoding failed")

        lat = geo["lat"]

        lon = geo["lon"]

    stores = search_nearby_stores(
        db=db,
        lat= lat,
        lon= lon,
        radius_miles=request.radius_miles,
        services=request.services,
        store_types=request.store_types,
        open_now=request.open_now,
    )

    return {
        "metadata": {
            "searched_location": {
                "lat": lat,
                "lon": lon,
            },
            "radius_miles": request.radius_miles,
            "services": request.services,
            "store_types": request.store_types,
            "open_now": request.open_now,
            "total_found": len(stores),
        },
        "stores": stores,
    }


@app.post("/api/auth/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_session),
):
    user = db.exec(select(User).where(User.email == request.email)).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    if not user.role:
        raise HTTPException(status_code=403, detail="User has no role assigned")

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user.must_change_password:
        raise HTTPException(
            status_code=403,
            detail="Password must be changed before login"
        )
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    refresh_token_record = RefreshToken(
        user_id=user.user_id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(refresh_token_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.post("/api/auth/refresh")
def refresh_access_token(
    request: RefreshRequest,
    db: Session = Depends(get_session),
):
    request_token_hash = hash_token(request.refresh_token)

    token_record = db.exec(
        select(RefreshToken).where(RefreshToken.token_hash == request_token_hash)
    ).first()

    if not token_record:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    if token_record.revoked:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token has expired")

    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.exec(select(User).where(User.user_id == payload["user_id"])).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    if not user.role:
        raise HTTPException(status_code=403, detail="User has no role assigned")

    new_access_token = create_access_token(user)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@app.post("/api/auth/logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_session),
):
    request_token_hash = hash_token(request.refresh_token)

    token_record = db.exec(
        select(RefreshToken).where(RefreshToken.token_hash == request_token_hash)
    ).first()

    if not token_record:
        raise HTTPException(status_code=404, detail="Refresh token not found")

    token_record.revoked = True

    db.add(token_record)
    db.commit()

    return {
        "message": "Logged out successfully"
    }


@app.post("/api/admin/stores")
def create_store(
    request: StoreCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permissions(["store:create"])),
):
    existing_store = db.exec(
        select(Store).where(Store.store_id == request.store_id)
    ).first()

    if existing_store:
        raise HTTPException(status_code=400, detail="Store already exists")

    lat = request.latitude
    lon = request.longitude

    if lat is None or lon is None:
        full_address = build_full_address(
            request.address_street,
            request.address_city,
            request.address_state,
            request.address_postal_code,
            request.address_country,
        )

        geo = geocode_address(full_address)

        if not geo:
            raise HTTPException(
                status_code=400,
                detail="Could not geocode store address. Please provide valid latitude and longitude.",
            )

        lat = geo["lat"]
        lon = geo["lon"]

    services = get_or_create_services(db, request.services)

    store_data = request.model_dump(exclude={"services", "latitude", "longitude"})

    store = Store(
        **store_data,
        latitude=lat,
        longitude=lon,
    )

    store.services = services

    db.add(store)
    db.commit()
    db.refresh(store)

    return {
        "store_id": store.store_id,
        "name": store.name,
        "store_type": store.store_type,
        "status": store.status,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "address_street": store.address_street,
        "address_city": store.address_city,
        "address_state": store.address_state,
        "address_postal_code": store.address_postal_code,
        "address_country": store.address_country,
        "phone": store.phone,
        "services": [service.name for service in store.services],
        "operating_hours": store.operating_hours,
    }

@app.get("/api/admin/stores")
def list_stores(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permissions(["store:read"])),
):
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")

    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    offset = (page - 1) * page_size

    statement = select(Store).offset(offset).limit(page_size)
    stores = db.exec(statement).all()

    return {
        "page": page,
        "page_size": page_size,
        "stores": [
            {
                "store_id": store.store_id,
                "name": store.name,
                "store_type": store.store_type,
                "status": store.status,
                "latitude": store.latitude,
                "longitude": store.longitude,
                "address_street": store.address_street,
                "address_city": store.address_city,
                "address_state": store.address_state,
                "address_postal_code": store.address_postal_code,
                "address_country": store.address_country,
                "phone": store.phone,
                "services": [service.name for service in store.services],
                "operating_hours": store.operating_hours,
            }
            for store in stores
        ],
    }


@app.get("/api/admin/stores/{store_id}")
def get_store(
    store_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permissions(["store:read"])),
):
    store = db.exec(
        select(Store).where(Store.store_id == store_id)
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    return {
        "store_id": store.store_id,
        "name": store.name,
        "store_type": store.store_type,
        "status": store.status,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "address_street": store.address_street,
        "address_city": store.address_city,
        "address_state": store.address_state,
        "address_postal_code": store.address_postal_code,
        "address_country": store.address_country,
        "phone": store.phone,
        "services": [service.name for service in store.services],
        "operating_hours": store.operating_hours,
    }


@app.patch("/api/admin/stores/{store_id}")
def update_store(
    store_id: str,
    request: StoreUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permissions(["store:update"])),
):
    store = db.exec(
        select(Store).where(Store.store_id == store_id)
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    update_data = request.model_dump(exclude_unset=True)

    allowed_fields = {"name", "phone", "services", "status", "operating_hours"}

    for field in update_data:
        if field not in allowed_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' is not allowed to be updated"
            )

    if "services" in update_data:
        store.services = get_or_create_services(db, update_data["services"])
        update_data.pop("services")

    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided for update"
        )
    for field, value in update_data.items():
        setattr(store, field, value)

    db.add(store)
    db.commit()
    db.refresh(store)

    return {
        "store_id": store.store_id,
        "name": store.name,
        "store_type": store.store_type,
        "status": store.status,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "address_street": store.address_street,
        "address_city": store.address_city,
        "address_state": store.address_state,
        "address_postal_code": store.address_postal_code,
        "address_country": store.address_country,
        "phone": store.phone,
        "services": [service.name for service in store.services],
        "operating_hours": store.operating_hours,
    }


@app.delete("/api/admin/stores/{store_id}")
def deactivate_store(
    store_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_permissions(["store:delete"])),
):
    store = db.exec(
        select(Store).where(Store.store_id == store_id)
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    store.status = "inactive"

    db.add(store)
    db.commit()
    db.refresh(store)

    return {
        "message": "Store deactivated successfully",
        "store_id": store.store_id,
        "status": store.status,
    }


@app.post("/api/admin/stores/import")
def import_stores(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user=Depends(require_permissions(["store:import"])),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        content = file.file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)

        # 1. validate CSV headers first
        validate_csv_headers(reader.fieldnames)

        created = 0
        updated = 0
        failed = []

        for idx, row in enumerate(reader, start=2):
            try:
                # 2. validate each row before saving
                validate_store_row(row)

                store_id = row["store_id"]

                service_names = row["services"].split("|") if row["services"] else []
                service_objects = get_or_create_services(db, service_names)
                operating_hours = {
                    "mon": row["hours_mon"],
                    "tue": row["hours_tue"],
                    "wed": row["hours_wed"],
                    "thu": row["hours_thu"],
                    "fri": row["hours_fri"],
                    "sat": row["hours_sat"],
                    "sun": row["hours_sun"],
                }
                lat_value = row["latitude"]

                lon_value = row["longitude"]

                if lat_value and lon_value:

                    latitude = float(lat_value)

                    longitude = float(lon_value)

                else:

                    full_address = build_full_address(

                        row["address_street"],

                        row["address_city"],

                        row["address_state"],

                        row["address_postal_code"],

                        row["address_country"],

                    )

                    geo = geocode_address(full_address)

                    if not geo:

                        raise ValueError(f"Could not geocode address for store_id={store_id}")

                    latitude = geo["lat"]

                    longitude = geo["lon"]
                existing_store = db.exec(
                    select(Store).where(Store.store_id == store_id)
                ).first()

                if existing_store:
                    # update existing store
                    existing_store.name = row["name"]
                    existing_store.store_type = row["store_type"]
                    existing_store.status = row["status"]
                    existing_store.latitude = latitude
                    existing_store.longitude = longitude
                    existing_store.address_street = row["address_street"]
                    existing_store.address_city = row["address_city"]
                    existing_store.address_state = row["address_state"]
                    existing_store.address_postal_code = row["address_postal_code"]
                    existing_store.address_country = row["address_country"]
                    existing_store.phone = row["phone"]
                    existing_store.services = service_objects
                    existing_store.operating_hours = operating_hours

                    db.add(existing_store)
                    updated += 1

                else:
                    # create new store
                    new_store = Store(
                        store_id=store_id,
                        name=row["name"],
                        store_type=row["store_type"],
                        status=row["status"],
                        latitude=latitude,
                        longitude=longitude,
                        address_street=row["address_street"],
                        address_city=row["address_city"],
                        address_state=row["address_state"],
                        address_postal_code=row["address_postal_code"],
                        address_country=row["address_country"],
                        phone=row["phone"],
                        operating_hours=operating_hours,
                    )
                    new_store.services = service_objects

                    db.add(new_store)
                    created += 1

            except Exception as e:
                failed.append({
                    "row": idx,
                    "store_id": row.get("store_id"),
                    "error": str(e),
                })

        # 3. all-or-nothing rule
        # If any row failed, rollback everything.
        if failed:
            db.rollback()
            return {
                "message": "Import failed. No data was saved.",
                "total_rows": created + updated + len(failed),
                "created": 0,
                "updated": 0,
                "failed": failed,
            }

        # 4. commit only if every row passed
        db.commit()

        return {
            "message": "Import completed successfully.",
            "total_rows": created + updated,
            "created": created,
            "updated": updated,
            "failed": [],
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import failed and was rolled back: {str(e)}"
        )


@app.post("/api/admin/users")
def create_user(
    request: UserCreate,
    db: Session = Depends(get_session),
    current_user=Depends(require_permissions(["user:create"])),
):
    existing_user = db.exec(
        select(User).where(User.email == request.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User email already exists")

    valid_statuses = {"active", "inactive"}
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    role = db.exec(
        select(Role).where(Role.name == request.role)
    ).first()

    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        user_id=request.user_id,
        email=request.email,
        hashed_password=hash_password(request.password),
        role_id=role.id,
        status=request.status,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": role.name,
        "status": user.status,
    }


@app.get("/api/admin/users")
def list_users(
    db: Session = Depends(get_session),
    current_user=Depends(require_permissions(["user:read"])),
):
    users = db.exec(select(User)).all()

    return [
        {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role.name if user.role else None,
            "status": user.status,
        }
        for user in users
    ]


@app.put("/api/admin/users/{user_id}")
def update_user(
    user_id: str,
    request: UserUpdate,
    db: Session = Depends(get_session),
    current_user=Depends(require_permissions(["user:update"])),
):
    user = db.exec(
        select(User).where(User.user_id == user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = request.model_dump(exclude_unset=True)

    if "role" in update_data:
        role = db.exec(
            select(Role).where(Role.name == update_data["role"])
        ).first()

        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")

        user.role_id = role.id

    if "status" in update_data:
        valid_statuses = {"active", "inactive"}
        if update_data["status"] not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        user.status = update_data["status"]

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "status": user.status,
    }


@app.delete("/api/admin/users/{user_id}")
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_session),
    current_user=Depends(require_permissions(["user:delete"])),
):
    user = db.exec(
        select(User).where(User.user_id == user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = "inactive"

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User deactivated successfully",
        "user_id": user.user_id,
        "status": user.status,
    }



@app.post("/api/auth/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_session),
):
    user = db.exec(
        select(User).where(User.email == request.email)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid current password")

    user.hashed_password = hash_password(request.new_password)
    user.must_change_password = False

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Password changed successfully. Please login again."
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)