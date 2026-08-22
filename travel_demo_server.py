"""A standalone, local-only travel discovery demo.

Run this module directly; it deliberately has no dependency on Hushh chat,
Gemini, authentication, a vault, or the application database.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "consent-protocol"))
load_dotenv(ROOT / "consent-protocol" / ".env", override=False)

from hushh_mcp.agents.travel.serpapi import SerpApiTravelClient, SerpApiTravelError  # noqa: E402

app = FastAPI(title="Hussh Travel Demo", docs_url=None, redoc_url=None)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    departure_date: date
    duration_days: int = Field(ge=1, le=30)

    @field_validator("origin", "destination")
    @classmethod
    def normalise_place(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("place must not be blank")
        return value


def _results(request: SearchRequest, flights: list[dict[str, str]], hotels: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "kind": "travel_results",
        "schema_version": "travel_results.v1",
        "mode": "serpapi_search_results",
        "trip": {
            "title": f"{request.duration_days}-day trip to {request.destination}",
            "origin": request.origin,
            "destination": request.destination,
            "date_label": request.departure_date.isoformat(),
            "duration_days": request.duration_days,
        },
        "timeline": [
            {"id": "departure", "kind": "transfer", "title": "Departure transfer", "detail": "Arrange your connection to the departure airport after choosing a flight."},
            {"id": "journey", "kind": "journey", "title": "Outbound journey", "detail": "Compare current flight snapshots before booking with a provider."},
            {"id": "arrival", "kind": "transfer", "title": "Arrival transfer", "detail": "Arrange a local transfer once your arrival time is confirmed."},
            {"id": "stay", "kind": "stay", "title": "Stay", "detail": "Compare stays for the trip dates below."},
        ],
        "option_groups": [
            {"id": "flights", "title": "Outbound flights", "subtitle": "Google Flights search results · prices can change.", "options": flights or [{"id": "flight", "label": "No flight options", "detail": "Try another airport or date."}]},
            {"id": "stays", "title": "Stays", "subtitle": "Google Hotels search results · verify before booking.", "options": hotels or [{"id": "hotel", "label": "No stay options", "detail": "Try another destination or date."}]},
        ],
        "notice": "Demo search results from SerpApi Google travel surfaces. Prices and availability can change; nothing has been booked.",
    }


@app.get("/")
async def landing() -> FileResponse:
    return FileResponse(Path(__file__).with_name("landing.html"), headers={"Cache-Control": "no-store"})


@app.get("/app")
async def index() -> FileResponse:
    return FileResponse(Path(__file__).with_name("index.html"), headers={"Cache-Control": "no-store"})


@app.post("/api/search")
async def search(body: SearchRequest) -> dict[str, Any]:
    if body.departure_date < date.today():
        raise HTTPException(status_code=422, detail="Choose a future departure date.")
    try:
        flights, hotels = await SerpApiTravelClient().search(
            origin=body.origin,
            destination=body.destination,
            departure_date=body.departure_date,
            duration_days=body.duration_days,
        )
    except SerpApiTravelError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _results(body, flights, hotels)
