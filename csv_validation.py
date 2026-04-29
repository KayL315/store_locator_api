import re

VALID_STORE_TYPES = {"flagship", "regular", "outlet", "express"}
VALID_STATUSES = {"active", "inactive", "temporarily_closed"}
VALID_SERVICES = {
    "pharmacy", "pickup", "returns", "optical",
    "photo_printing", "gift_wrapping", "automotive", "garden_center"
}

REQUIRED_COLUMNS = [
    "store_id", "name", "store_type", "status", "latitude", "longitude",
    "address_street", "address_city", "address_state", "address_postal_code",
    "address_country", "phone", "services",
    "hours_mon", "hours_tue", "hours_wed", "hours_thu",
    "hours_fri", "hours_sat", "hours_sun"
]


def validate_csv_headers(headers):
    if headers != REQUIRED_COLUMNS:
        raise ValueError("CSV headers do not match required format")


def validate_hours(value: str):
    if value == "closed":
        return True

    pattern = r"^\d{2}:\d{2}-\d{2}:\d{2}$"

    if not re.match(pattern, value):
        raise ValueError(f"Invalid hours format: {value}")

    open_time, close_time = value.split("-")

    if open_time >= close_time:
        raise ValueError(f"Open time must be earlier than close time: {value}")

    return True


def validate_store_row(row):
    if not re.match(r"^S\d{4}$", row["store_id"]):
        raise ValueError("Invalid store_id format")

    if row["store_type"] not in VALID_STORE_TYPES:
        raise ValueError("Invalid store_type")

    if row["status"] not in VALID_STATUSES:
        raise ValueError("Invalid status")

    lat = float(row["latitude"])
    lon = float(row["longitude"])

    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if not re.match(r"^[A-Z]{2}$", row["address_state"]):
        raise ValueError("address_state must be 2 uppercase letters")

    if not re.match(r"^\d{5}$", row["address_postal_code"]):
        raise ValueError("address_postal_code must be 5 digits")

    if row["address_country"] != "USA":
        raise ValueError("address_country must be USA")

    if not re.match(r"^\d{3}-\d{3}-\d{4}$", row["phone"]):
        raise ValueError("Invalid phone format")

    services = row["services"].split("|") if row["services"] else []

    for service in services:
        if service not in VALID_SERVICES:
            raise ValueError(f"Invalid service: {service}")

    for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        validate_hours(row[f"hours_{day}"])