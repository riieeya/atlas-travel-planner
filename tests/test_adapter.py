import pytest
from serpapi_adapter import SerpApiTravelError, airport_id

@pytest.mark.parametrize(("value", "expected"), [
    ("Mumbai", "BOM"), ("bengaluru", "BLR"), ("DXB", "DXB"), (" Paris ", "CDG"),
])
def test_airport_resolution(value, expected):
    assert airport_id(value) == expected

def test_unknown_city_requests_an_airport_code():
    with pytest.raises(SerpApiTravelError, match="3-letter airport code"):
        airport_id("Unknown place")

def test_expanded_airport_catalogue():
    assert airport_id("Cape Town") == "CPT"
    assert airport_id("Ho Chi Minh City") == "SGN"
