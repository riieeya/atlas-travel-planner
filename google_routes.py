"""Small, server-side Google Routes API adapter for Atlas."""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx

ROUTES_ENDPOINT = "https://routes.googleapis.com/directions/v2:computeRoutes"
FIELD_MASK = (
    "routes.duration,routes.distanceMeters,routes.staticDuration,"
    "routes.travelAdvisory.tollInfo"
)
TravelMode = Literal["DRIVE", "WALK", "BICYCLE", "TWO_WHEELER"]


class GoogleRoutesError(RuntimeError):
    """A safe, user-facing Routes failure."""


@dataclass
class _CacheEntry:
    expires_at: float
    value: dict[str, Any]


class GoogleRoutesClient:
    _cache: dict[str, _CacheEntry] = {}
    _lock = asyncio.Lock()

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 12) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_ROUTES_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self.cache_seconds = int(os.getenv("ATLAS_ROUTES_CACHE_SECONDS", "300"))

    async def estimate(
        self, *, origin: str, destination: str, travel_mode: TravelMode,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise GoogleRoutesError(
                "Route estimates are not configured. Add GOOGLE_MAPS_ROUTES_API_KEY to .env."
            )
        cache_key = f"{origin.casefold()}:{destination.casefold()}:{travel_mode}"
        cached = self._cache.get(cache_key)
        if cached and cached.expires_at > time.monotonic():
            return cached.value

        payload = {
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": travel_mode,
            "routingPreference": "TRAFFIC_AWARE" if travel_mode == "DRIVE" else "TRAFFIC_UNAWARE",
            "units": "METRIC",
        }
        headers = {"X-Goog-Api-Key": self.api_key, "X-Goog-FieldMask": FIELD_MASK}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(ROUTES_ENDPOINT, json=payload, headers=headers)
                response.raise_for_status()
                routes = response.json().get("routes") or []
        except (httpx.HTTPError, ValueError) as exc:
            raise GoogleRoutesError("Route estimates are temporarily unavailable.") from exc
        if not routes:
            raise GoogleRoutesError("No route was found for those locations.")

        route = routes[0]
        value = {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "duration_seconds": _duration_seconds(route.get("duration")),
            "static_duration_seconds": _duration_seconds(route.get("staticDuration")),
            "distance_meters": route.get("distanceMeters"),
            "has_tolls": bool(route.get("travelAdvisory", {}).get("tollInfo")),
            "source": "google_routes",
            "notice": "Estimate only. Recheck pickup, traffic, tolls and accessibility before leaving.",
        }
        async with self._lock:
            self._cache[cache_key] = _CacheEntry(time.monotonic() + self.cache_seconds, value)
        return value


def _duration_seconds(value: Any) -> int | None:
    if not isinstance(value, str) or not value.endswith("s"):
        return None
    try:
        return round(float(value[:-1]))
    except ValueError:
        return None
