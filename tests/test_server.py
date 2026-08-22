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
