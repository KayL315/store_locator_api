import pytest

from csv_validation import (
    validate_csv_headers,
    validate_store_row,
    REQUIRED_COLUMNS,
)


def valid_row():
    return {
        "store_id": "S0001",
        "name": "Boston Store",
        "store_type": "regular",
        "status": "active",
        "latitude": "42.3601",
        "longitude": "-71.0589",
        "address_street": "100 Main St",
        "address_city": "Boston",
        "address_state": "MA",
        "address_postal_code": "02101",
        "address_country": "USA",
        "phone": "617-555-0100",
        "services": "pickup|pharmacy",
        "hours_mon": "08:00-22:00",
        "hours_tue": "08:00-22:00",
        "hours_wed": "08:00-22:00",
        "hours_thu": "08:00-22:00",
        "hours_fri": "08:00-22:00",
        "hours_sat": "09:00-21:00",
        "hours_sun": "closed",
    }


def test_validate_csv_headers_success():
    validate_csv_headers(REQUIRED_COLUMNS)


def test_validate_csv_headers_fail():
    bad_headers = REQUIRED_COLUMNS[:-1]

    with pytest.raises(ValueError):
        validate_csv_headers(bad_headers)


def test_validate_store_row_success():
    validate_store_row(valid_row())


def test_validate_store_row_invalid_store_id():
    row = valid_row()
    row["store_id"] = "BAD001"

    with pytest.raises(ValueError):
        validate_store_row(row)


def test_validate_store_row_invalid_store_type():
    row = valid_row()
    row["store_type"] = "superstore"

    with pytest.raises(ValueError):
        validate_store_row(row)


def test_validate_store_row_invalid_latitude():
    row = valid_row()
    row["latitude"] = "100"

    with pytest.raises(ValueError):
        validate_store_row(row)


def test_validate_store_row_invalid_service():
    row = valid_row()
    row["services"] = "pickup|invalid_service"

    with pytest.raises(ValueError):
        validate_store_row(row)