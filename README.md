# Atlas Travel Planner

Atlas is a local-first travel-planning prototype. It searches flight and hotel snapshots, then lets you keep an itinerary, manual budget, packing list, and saved plans in the browser.

It does not make reservations, process payments, create accounts, or store travel plans on a server.

## Current capabilities

- Flight and hotel discovery through SerpApi's Google travel search surfaces
- Consent prompt before a live search
- Day-by-day itinerary board
- Local-browser budget and packing checklist
- Landing page and planner workspace

## Run locally

This first version currently reuses the Hushh travel search adapter from the parent `hushh-research` checkout. Keep this folder next to `consent-protocol` until the adapter is extracted.

1. In the parent `consent-protocol/.env`, set:

   ```env
   SERPAPI_API_KEY=your_key
   HUSHH_TRAVEL_SERPAPI_ENABLED=true
   ```

2. Start the app from this directory:

   ```powershell
   ..\consent-protocol\.venv\Scripts\python.exe -m uvicorn travel_demo_server:app --host 127.0.0.1 --port 3001
   ```

3. Open `http://127.0.0.1:3001`.

## Data and privacy

- Only the trip fields entered in the form are sent to SerpApi when the search checkbox is confirmed.
- Saved itinerary, budget, and checklist data stays in the browser's local storage.
- Search results are snapshots only; availability and prices can change.

## Roadmap

The next extraction will make the SerpApi adapter and environment configuration self-contained so Atlas can run from this repository alone.
