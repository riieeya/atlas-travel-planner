import pytest

from google_routes import GoogleRoutesClient, GoogleRoutesError, _duration_seconds


def test_parses_google_duration():
    assert _duration_seconds("123.5s") == 124
    assert _duration_seconds("not-a-duration") is None


@pytest.mark.asyncio
async def test_routes_requires_key():
    with pytest.raises(GoogleRoutesError, match="GOOGLE_MAPS_ROUTES_API_KEY"):
        await GoogleRoutesClient(api_key="").estimate(
            origin="Mumbai Airport", destination="Bandra", travel_mode="DRIVE"
        )
