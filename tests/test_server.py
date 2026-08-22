from datetime import date, timedelta
from fastapi.testclient import TestClient
from travel_demo_server import app
client = TestClient(app)
def test_health(): assert client.get("/api/health").json()["status"] == "ok"
def test_past_date_is_rejected():
    r=client.post("/api/search",json={"origin":"BOM","destination":"DXB","departure_date":(date.today()-timedelta(days=1)).isoformat(),"duration_days":3})
    assert r.status_code==422
def test_handoff_requires_confirmation():
    r=client.post("/api/handoff",json={"provider":"google_flights","origin":"BOM","destination":"DXB","departure_date":(date.today()+timedelta(days=30)).isoformat(),"confirmed":False})
    assert r.status_code==422
def test_handoff_is_allowlisted():
    r=client.post("/api/handoff",json={"provider":"google_hotels","origin":"BOM","destination":"Dubai","departure_date":(date.today()+timedelta(days=30)).isoformat(),"confirmed":True})
    assert r.status_code==200 and r.json()["url"].startswith("https://www.google.com/travel/hotels?")
def test_invalid_passenger_count_is_rejected_before_provider_call():
    r=client.post("/api/search",json={"origin":"BOM","destination":"DXB","departure_date":(date.today()+timedelta(days=30)).isoformat(),"duration_days":3,"adults":0})
    assert r.status_code==422
def test_invalid_currency_is_rejected_before_provider_call():
    r=client.post("/api/search",json={"origin":"BOM","destination":"DXB","departure_date":(date.today()+timedelta(days=30)).isoformat(),"duration_days":3,"currency":"XYZ"})
    assert r.status_code==422
def test_round_trip_requires_return_date():
    r=client.post("/api/search",json={"origin":"BOM","destination":"DXB","departure_date":(date.today()+timedelta(days=30)).isoformat(),"duration_days":3,"trip_type":"round_trip"})
    assert r.status_code==422
def test_return_date_must_follow_departure():
    departure=date.today()+timedelta(days=30)
    r=client.post("/api/search",json={"origin":"BOM","destination":"DXB","departure_date":departure.isoformat(),"return_date":departure.isoformat(),"duration_days":3,"trip_type":"round_trip"})
    assert r.status_code==422
def test_airport_autocomplete_returns_codes():
    r=client.get("/api/airports",params={"q":"mumb"})
    assert r.status_code==200
    assert r.json()["airports"][0]["code"]=="BOM"
def test_airport_autocomplete_rejects_short_queries():
    assert client.get("/api/airports",params={"q":"m"}).status_code==422
