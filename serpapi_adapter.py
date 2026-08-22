"""Small, self-contained SerpApi travel adapter for Atlas."""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import httpx

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
AIRPORT_ALIASES = {
    "mumbai": "BOM", "bombay": "BOM", "delhi": "DEL", "new delhi": "DEL",
    "bangalore": "BLR", "bengaluru": "BLR", "chennai": "MAA", "kolkata": "CCU",
    "hyderabad": "HYD", "dubai": "DXB", "london": "LHR", "paris": "CDG",
    "new york": "JFK", "singapore": "SIN", "tokyo": "HND", "bangkok": "BKK",
    "sydney": "SYD", "toronto": "YYZ", "rome": "FCO", "amsterdam": "AMS",
    "ahmedabad": "AMD", "pune": "PNQ", "goa": "GOI", "kochi": "COK",
    "cochin": "COK", "jaipur": "JAI", "lucknow": "LKO", "chandigarh": "IXC",
    "guwahati": "GAU", "bhubaneswar": "BBI", "indore": "IDR", "nagpur": "NAG",
    "newark": "EWR", "los angeles": "LAX", "san francisco": "SFO",
    "chicago": "ORD", "miami": "MIA", "boston": "BOS", "seattle": "SEA",
    "washington": "IAD", "vancouver": "YVR", "montreal": "YUL",
    "barcelona": "BCN", "madrid": "MAD", "lisbon": "LIS", "berlin": "BER",
    "munich": "MUC", "frankfurt": "FRA", "zurich": "ZRH", "vienna": "VIE",
    "prague": "PRG", "athens": "ATH", "istanbul": "IST", "doha": "DOH",
    "abu dhabi": "AUH", "riyadh": "RUH", "jeddah": "JED", "muscat": "MCT",
    "hong kong": "HKG", "seoul": "ICN", "osaka": "KIX", "kuala lumpur": "KUL",
    "bali": "DPS", "jakarta": "CGK", "manila": "MNL", "hanoi": "HAN",
    "ho chi minh city": "SGN", "melbourne": "MEL", "auckland": "AKL",
    "cairo": "CAI", "nairobi": "NBO", "cape town": "CPT", "johannesburg": "JNB",
    "maldives": "MLE", "mauritius": "MRU", "colombo": "CMB", "kathmandu": "KTM",
}


class SerpApiTravelError(RuntimeError):
    pass


def airport_id(value: str) -> str:
    cleaned = " ".join(value.split()).strip()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned.upper()
    code = AIRPORT_ALIASES.get(cleaned.casefold())
    if code:
        return code
    raise SerpApiTravelError(
        f'Use a 3-letter airport code for "{cleaned}" (for example BOM or DXB).'
    )


def _price(value: Any, currency: str = "USD") -> str:
    if isinstance(value, (int, float)):
        return f"{currency} {value:,.0f}"
    return str(value or "Price unavailable")


@dataclass
class _CacheEntry:
    expires_at: float
    value: tuple[list[dict[str, Any]], list[dict[str, Any]]]


class SerpApiTravelClient:
    _cache: dict[str, _CacheEntry] = {}
    _lock = asyncio.Lock()

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 18) -> None:
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self.cache_seconds = int(os.getenv("ATLAS_SEARCH_CACHE_SECONDS", "600"))

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise SerpApiTravelError("Live search is not configured. Add SERPAPI_API_KEY to .env.")
        params = {**params, "api_key": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(SERPAPI_ENDPOINT, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SerpApiTravelError("The travel provider is temporarily unavailable.") from exc
        if payload.get("error"):
            raise SerpApiTravelError(str(payload["error"]))
        return payload

    async def search(
        self, *, origin: str, destination: str, departure_date: date, duration_days: int,
        adults: int = 1, children: int = 0, travel_class: int = 1,
        stops: int = 0, currency: str = "USD", trip_type: str = "one_way",
        return_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        departure = airport_id(origin)
        arrival = airport_id(destination)
        cache_key = f"{departure}:{arrival}:{departure_date}:{return_date}:{duration_days}:{adults}:{children}:{travel_class}:{stops}:{currency}"
        cached = self._cache.get(cache_key)
        if cached and cached.expires_at > time.monotonic():
            return cached.value

        checkout = departure_date + timedelta(days=duration_days)
        flights_payload, hotels_payload = await asyncio.gather(
            self._get({
                "engine": "google_flights", "departure_id": departure,
                "arrival_id": arrival, "outbound_date": departure_date.isoformat(),
                "type": "1" if trip_type == "round_trip" else "2",
                **({"return_date": return_date.isoformat()} if return_date else {}),
                "currency": currency, "hl": "en", "adults": adults,
                "children": children, "travel_class": travel_class, "stops": stops,
            }),
            self._get({
                "engine": "google_hotels", "q": destination,
                "check_in_date": departure_date.isoformat(),
                "check_out_date": checkout.isoformat(), "currency": currency,
                "adults": adults, "children": children, "hl": "en",
            }),
        )
        value = (self._flights(flights_payload), self._hotels(hotels_payload))
        async with self._lock:
            self._cache[cache_key] = _CacheEntry(time.monotonic() + self.cache_seconds, value)
            if len(self._cache) > 64:
                self._cache = {
                    key: item for key, item in self._cache.items()
                    if item.expires_at > time.monotonic()
                }
        return value

    @staticmethod
    def _flights(payload: dict[str, Any]) -> list[dict[str, Any]]:
        groups = [*payload.get("best_flights", []), *payload.get("other_flights", [])][:8]
        currency = payload.get("search_parameters", {}).get("currency", "USD")
        results: list[dict[str, Any]] = []
        for index, group in enumerate(groups):
            legs = group.get("flights") or []
            first, last = (legs[0] if legs else {}), (legs[-1] if legs else {})
            airline = first.get("airline") or "Flight option"
            results.append({
                "id": f"flight-{index}",
                "kind": "flight",
                "label": airline,
                "detail": f"{first.get('departure_airport', {}).get('time', 'Time TBA')} → {last.get('arrival_airport', {}).get('time', 'Time TBA')} · {len(legs)-1 if legs else 0} stop(s)",
                "price": _price(group.get("price"), currency),
                "duration": f"{group.get('total_duration', '—')} min",
                "duration_minutes": group.get("total_duration"),
                "stops": max(0, len(legs) - 1),
                "departure_time": first.get("departure_airport", {}).get("time"),
                "arrival_time": last.get("arrival_airport", {}).get("time"),
                "departure_airport": first.get("departure_airport", {}).get("id"),
                "arrival_airport": last.get("arrival_airport", {}).get("id"),
                "layovers": [{"airport": stop.get("id"), "name": stop.get("name"), "duration_minutes": stop.get("duration")} for stop in group.get("layovers", [])],
                "emissions_grams": group.get("carbon_emissions", {}).get("this_flight"),
                "price_value": group.get("price"),
                "image": first.get("airline_logo"),
            })
        return results

    @staticmethod
    def _hotels(payload: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        currency = payload.get("search_parameters", {}).get("currency", "USD")
        for index, item in enumerate((payload.get("properties") or [])[:8]):
            rate = item.get("rate_per_night") or {}
            image = next(iter(item.get("images") or []), {}).get("thumbnail")
            results.append({
                "id": f"hotel-{index}",
                "kind": "hotel",
                "label": item.get("name") or "Stay option",
                "detail": f"{item.get('overall_rating', 'New')} rating · {item.get('type', 'Property')}",
                "price": rate.get("lowest") or _price(rate.get("extracted_lowest"), currency),
                "duration": f"{item.get('reviews', 0)} reviews",
                "price_value": rate.get("extracted_lowest"),
                "rating": item.get("overall_rating"),
                "reviews": item.get("reviews", 0),
                "image": image,
            })
        return results
