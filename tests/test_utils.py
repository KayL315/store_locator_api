from search_logic import calculate_bounding_box, get_exact_distance, is_store_open
from csv_validation import validate_hours


def test_calculate_bounding_box():
    bbox = calculate_bounding_box(42.3601, -71.0589, 10)

    assert bbox["min_lat"] < 42.3601
    assert bbox["max_lat"] > 42.3601
    assert bbox["min_lon"] < -71.0589
    assert bbox["max_lon"] > -71.0589


def test_distance_calculation():
    boston = (42.3601, -71.0589)
    cambridge = (42.3736, -71.1097)

    distance = get_exact_distance(boston, cambridge)

    assert distance > 0
    assert distance < 10


def test_validate_hours_valid():
    assert validate_hours("08:00-22:00") is True
    assert validate_hours("closed") is True


def test_validate_hours_invalid_order():
    try:
        validate_hours("22:00-08:00")
        assert False
    except ValueError:
        assert True


def test_is_store_open_closed_day():
    hours = {
        "mon": "closed",
        "tue": "closed",
        "wed": "closed",
        "thu": "closed",
        "fri": "closed",
        "sat": "closed",
        "sun": "closed",
    }

    assert is_store_open(hours) is False