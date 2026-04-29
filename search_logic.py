import math
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from geopy.distance import geodesic
from sqlmodel import Session, select, and_

from models import Store


def calculate_bounding_box(lat: float, lon: float, radius_miles: float) -> dict:
    """
    Calculate a square bounding box around the search point.
    This is used for the first database-level filter.
    """
    lat_delta = radius_miles / 69.0

    # Avoid division by zero near the poles.
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 0.00001:
        lon_delta = 180
    else:
        lon_delta = radius_miles / (69.0 * cos_lat)

    return {
        "min_lat": max(lat - lat_delta, -90),
        "max_lat": min(lat + lat_delta, 90),
        "min_lon": max(lon - lon_delta, -180),
        "max_lon": min(lon + lon_delta, 180),
    }


def get_exact_distance(user_coords: Tuple[float, float], store_coords: Tuple[float, float]) -> float:
    """
    Calculate exact distance in miles using geopy.
    """
    return geodesic(user_coords, store_coords).miles


def is_store_open(operating_hours: Optional[dict]) -> bool:
    """
    Check if a store is open right now based on operating_hours JSON.

    Expected format:
    {
        "mon": "08:00-22:00",
        "tue": "08:00-22:00",
        ...
        "sun": "closed"
    }
    """
    if not operating_hours:
        return False

    now = datetime.now()
    current_day = now.strftime("%a").lower()  # mon, tue, wed...
    current_time = now.strftime("%H:%M")

    today_hours = operating_hours.get(current_day)

    if not today_hours or today_hours.lower() == "closed":
        return False

    try:
        open_time, close_time = today_hours.split("-")
        return open_time <= current_time <= close_time
    except ValueError:
        return False


def store_matches_services(store_services: Optional[List[str]], required_services: Optional[List[str]]) -> bool:
    """
    services filter uses AND logic.
    Example:
    required_services = ["pickup", "pharmacy"]
    Store must contain both pickup and pharmacy.
    """
    if not required_services:
        return True

    if not store_services:
        return False

    return all(service in store_services for service in required_services)


def store_matches_type(store_type: str, store_types: Optional[List[str]]) -> bool:
    """
    store_types filter uses OR logic.
    Example:
    store_types = ["regular", "flagship"]
    Store can be regular OR flagship.
    """
    if not store_types:
        return True

    return store_type in store_types


def search_nearby_stores(
    db: Session,
    lat: float,
    lon: float,
    radius_miles: float = 10.0,
    services: Optional[List[str]] = None,
    store_types: Optional[List[str]] = None,
    open_now: bool = False,
) -> List[Dict[str, Any]]:
    """
    Main search function.

    Steps:
    1. Calculate bounding box.
    2. Query stores inside bounding box.
    3. Calculate exact distance using geopy.
    4. Apply radius filter.
    5. Apply services/store_types/open_now filters.
    6. Sort by distance.
    """
    bbox = calculate_bounding_box(lat, lon, radius_miles)

    statement = select(Store).where(
        and_(
            Store.latitude >= bbox["min_lat"],
            Store.latitude <= bbox["max_lat"],
            Store.longitude >= bbox["min_lon"],
            Store.longitude <= bbox["max_lon"],
            Store.status == "active",
        )
    )

    candidate_stores = db.exec(statement).all()

    results = []
    user_location = (lat, lon)

    for store in candidate_stores:
        distance = get_exact_distance(
            user_location,
            (store.latitude, store.longitude),
        )

        if distance > radius_miles:
            continue

        if not store_matches_services(store.services, services):
            continue

        if not store_matches_type(store.store_type, store_types):
            continue

        is_open = is_store_open(store.operating_hours)

        if open_now and not is_open:
            continue

        results.append(
            {
                "store_id": store.store_id,
                "name": store.name,
                "store_type": store.store_type,
                "status": store.status,
                "phone": store.phone,
                "latitude": store.latitude,
                "longitude": store.longitude,
                "address_street": store.address_street,
                "address_city": store.address_city,
                "address_state": store.address_state,
                "address_postal_code": store.address_postal_code,
                "address_country": store.address_country,
                "services": store.services,
                "operating_hours": store.operating_hours,
                "distance_miles": round(distance, 2),
                "is_open_now": is_open,
            }
        )

    results.sort(key=lambda store: store["distance_miles"])
    return results