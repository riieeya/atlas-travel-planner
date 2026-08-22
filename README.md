# Atlas Travel Planner

Atlas is a standalone, local-first travel-planning workspace. It discovers flight and hotel snapshots through SerpApi, then keeps comparison, shortlists, itinerary, budget, packing and trip readiness in the browser.

Atlas does **not** reserve inventory, guarantee prices, process payments or create accounts.

## Product workflow

1. Discover — enter the route and dates after an informed disclosure.
2. Compare — review normalized flight and stay cards.
3. Shortlist — keep promising candidates locally.
4. Itinerary — build the trip day by day.
5. Prepare — estimate spending and complete packing.
6. Ready — review progress and deliberately continue to an allowlisted provider.

## Architecture

- `travel_demo_server.py` — standalone FastAPI app, validation, rate limiting and provider handoffs.
- `serpapi_adapter.py` — Atlas-owned async adapter with normalized results and a short cache.
- `landing.html` and `index.html` — semantic page structure.
- `assets/styles.css` — shared design system and workspace UI.
- `assets/landing.css` — landing-page composition.
- `assets/app.js` — hash routing, local persistence and interactions.
- `tests/` — backend contract and security-boundary tests.

There is no import from Hushh and no dependency on a parent checkout.

Workspace state uses schema version 3. Atlas automatically migrates the earlier v2
workspace key when it is first opened after an upgrade.

Search controls currently include adults, children, cabin class, maximum stops
and display currency. These values are validated on the server before being sent
to SerpApi.

## Run locally

1. Create and activate a virtual environment:

       py -m venv .venv
       .\.venv\Scripts\Activate.ps1

2. Install dependencies:

       pip install -r requirements-dev.txt

3. Copy the environment template:

       Copy-Item .env.example .env

4. Put your private SerpApi key in `.env`. Never commit that file.

5. Start Atlas:

       uvicorn travel_demo_server:app --host 127.0.0.1 --port 3001 --reload

6. Open `http://127.0.0.1:3001`.

## Tests

    pytest -q

GitHub Actions runs tests and Python compilation on pushes and pull requests.

## Privacy and provider boundary

- Only submitted route and date fields go to SerpApi during live search.
- Planning state is stored in browser local storage.
- The server accepts a typed provider identifier, never an arbitrary redirect URL.
- Provider handoffs use fixed Google Travel hosts and require explicit confirmation.
- Prices and availability must be rechecked with the provider.

## Next product work

- Expand airport resolution beyond the starter city aliases.
- Add round-trip and flexible-date discovery.
- Add versioned migration for future local workspace schemas.
- Add official supplier integrations only after product, legal and support ownership is decided.
- Keep deeper Hushh integration paused until this standalone architecture is validated.
