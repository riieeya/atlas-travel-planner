"""Atlas standalone FastAPI application."""
from __future__ import annotations
import os, time
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from serpapi_adapter import SerpApiTravelClient, SerpApiTravelError

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)
app = FastAPI(title="Atlas Travel Planner", docs_url="/api/docs", redoc_url=None)
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
_requests: dict[str, deque[float]] = defaultdict(deque)

class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    departure_date: date
    duration_days: int = Field(ge=1, le=30)
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    travel_class: Literal[1, 2, 3, 4] = 1
    stops: Literal[0, 1, 2, 3] = 0
    currency: Literal["USD", "INR", "EUR", "GBP", "AED", "SGD", "JPY"] = "USD"
    @field_validator("origin", "destination")
    @classmethod
    def normalise_place(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value: raise ValueError("place must not be blank")
        return value

class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["google_flights", "google_hotels"]
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    departure_date: date
    confirmed: Literal[True]

def _rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "unknown"
    now, window = time.monotonic(), _requests[key]
    while window and window[0] < now - 60: window.popleft()
    if len(window) >= int(os.getenv("ATLAS_SEARCHES_PER_MINUTE", "15")):
        raise HTTPException(429, "Too many searches. Please wait a minute and try again.")
    window.append(now)

def destination_brief(destination: str) -> dict[str, str]:
    briefs = {
        "dubai": {"accent":"desert","timezone":"GST · UTC+4","currency":"AED","tip":"October to March is generally the most comfortable season."},
        "london": {"accent":"city","timezone":"GMT/BST","currency":"GBP","tip":"Keep rain protection handy in every season."},
        "paris": {"accent":"rose","timezone":"CET/CEST","currency":"EUR","tip":"Reserve major museums before your travel day."},
        "singapore": {"accent":"tropical","timezone":"SGT · UTC+8","currency":"SGD","tip":"Plan for warm weather and short tropical showers."},
        "tokyo": {"accent":"sakura","timezone":"JST · UTC+9","currency":"JPY","tip":"A rechargeable transit card simplifies local movement."},
    }
    return briefs.get(destination.casefold(), {"accent":"ocean","timezone":"Check local time","currency":"Check local currency","tip":"Verify entry rules, weather and local transport before departure."})

def _results(body: SearchRequest, flights: list[dict[str, Any]], hotels: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "kind":"travel_results","schema_version":"travel_results.v2",
        "trip":{"title":f"{body.duration_days}-night trip to {body.destination}","origin":body.origin,"destination":body.destination,"date_label":body.departure_date.isoformat(),"duration_days":body.duration_days,"adults":body.adults,"children":body.children,"travel_class":body.travel_class,"stops":body.stops,"currency":body.currency},
        "destination":destination_brief(body.destination),
        "timeline":[{"title":"Discover","detail":"Live flight and stay snapshots"},{"title":"Compare","detail":"Shortlist the strongest options"},{"title":"Organize","detail":"Build the days around your choices"},{"title":"Prepare","detail":"Budget, packing and transfers"}],
        "option_groups":[{"id":"flights","title":"Outbound flights","subtitle":"Current Google Flights snapshots","options":flights},{"id":"stays","title":"Stays","subtitle":"Current Google Hotels snapshots","options":hotels}],
        "notice":"Search snapshots only. Prices and availability can change; nothing has been booked.",
    }

@app.get("/")
async def landing() -> FileResponse:
    return FileResponse(ROOT / "landing.html", headers={"Cache-Control":"no-store"})
@app.get("/app")
async def workspace() -> FileResponse:
    return FileResponse(ROOT / "index.html", headers={"Cache-Control":"no-store"})
@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status":"ok","service":"atlas"}
@app.post("/api/search")
async def search(body: SearchRequest, request: Request) -> dict[str, Any]:
    _rate_limit(request)
    if body.departure_date < date.today(): raise HTTPException(422, "Choose a future departure date.")
    try:
        flights, hotels = await SerpApiTravelClient().search(origin=body.origin,destination=body.destination,departure_date=body.departure_date,duration_days=body.duration_days,adults=body.adults,children=body.children,travel_class=body.travel_class,stops=body.stops,currency=body.currency)
    except SerpApiTravelError as exc:
        raise HTTPException(503, str(exc)) from exc
    return _results(body, flights, hotels)
@app.post("/api/handoff")
async def handoff(body: HandoffRequest) -> dict[str, str]:
    if body.provider == "google_flights":
        url = "https://www.google.com/travel/flights?" + urlencode({"q":f"Flights from {body.origin} to {body.destination} on {body.departure_date.isoformat()}"})
    else:
        url = "https://www.google.com/travel/hotels?" + urlencode({"q":f"Hotels in {body.destination} from {body.departure_date.isoformat()}"})
    return {"provider":body.provider,"url":url,"notice":"You are leaving Atlas. Recheck price and availability with the provider."}
