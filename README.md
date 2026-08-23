# Atlas Travel Planner

Atlas is a modern, standalone and local-first travel-planning workspace. It brings flight and hotel discovery, comparison, shortlisting, itinerary design, budgeting, packing and trip readiness into one clear workflow.

Atlas is currently a planning and discovery prototype. It does **not** reserve inventory, guarantee prices, process payments or claim that a booking has been completed.

## Why Atlas

Travel planning is usually spread across search tabs, notes, spreadsheets and screenshots. Atlas organizes that work into six understandable stages:

1. **Discover** — choose a route, dates, passengers and preferences.
2. **Compare** — review normalized flight and hotel snapshots.
3. **Shortlist** — save the strongest candidates locally.
4. **Itinerary** — create a timed, day-by-day plan.
5. **Prepare** — estimate spending and complete packing.
6. **Ready** — review trip progress and deliberately continue to a provider.

## Current features

### Travel discovery

- One-way and round-trip searches
- Return-date validation
- Flexible-date windows from exact date through ±3 days
- Adults and children
- Economy, premium economy, business and first class
- Stop filters
- INR, USD, EUR, GBP, AED, SGD and JPY
- Origin and destination swap control
- Persistent search filters
- Local recent-search history

### Airport discovery

- Autocomplete after two characters
- More than 60 starter city and airport aliases
- Major Indian and international destinations
- Direct three-letter airport-code entry
- Debounced requests and duplicate removal

### Flights and stays

- Structured flight and hotel cards
- Airline and hotel imagery when supplied by SerpApi
- Departure and arrival information
- Total duration and number of stops
- Layover airport and duration
- Estimated flight emissions when available
- Hotel rating and review count
- Shortlisting and selected-state feedback
- Sorting by price, duration and stops
- Nonstop and rated-stay filters
- Loading skeletons and recovery guidance

### Flexible-date comparison

- Visible nearby-date chips
- User-initiated searches for another date
- Lowest observed fare remembered for searched dates
- No automatic background multiplication of provider searches

### Intelligent itinerary

- Timed activities
- Calculated end times
- Activity categories
- Duration and travel-before buffers
- Automatic overlap detection
- Insufficient-transfer warnings
- Large schedule-gap warnings
- Drag-and-drop movement within and between days
- Mobile and keyboard-friendly earlier/later controls
- Destination-aware starter suggestions

### Planning tools

- Categorized trip budget
- Automatic planned-spend total
- Packing checklist
- Trip-readiness percentage
- Local `.ics` calendar export for timed itinerary activities
- Shortlist, itinerary, budget and packing persistence
- Responsive desktop, tablet and mobile layouts

### Provider handoff

- Explicit confirmation dialog
- Typed provider identifier
- Fixed, allowlisted Google Travel hosts
- No arbitrary client-supplied redirect URL
- Reminder to recheck price and availability
- External opening with `noopener` and `noreferrer`

## Architecture

Atlas no longer imports code or environment configuration from Hushh.

| Path | Responsibility |
|---|---|
| `travel_demo_server.py` | FastAPI app, request validation, rate limiting, static files and provider handoffs |
| `serpapi_adapter.py` | Async SerpApi integration, airport resolution, caching and normalized travel results |
| `landing.html` | Product landing page |
| `index.html` | Workspace structure |
| `assets/styles.css` | Shared design system and responsive layout |
| `assets/landing.css` | Landing-page presentation |
| `assets/comparison.css` | Date chips, comparison controls and loading states |
| `assets/itinerary.css` | Intelligent itinerary and suggestion presentation |
| `assets/app.js` | Routing, persistence, comparisons, itinerary and handoff interactions |
| `tests/` | API, adapter, security-boundary and static-integration tests |

## Local data model

Atlas uses browser local storage rather than an account or server-side user database.

The current workspace key is:

    atlas.workspace.v4

Older v3, v2 and original local-trip data is migrated automatically. Existing string-only itinerary activities are converted into structured timed activities.

Clearing browser storage removes locally saved Atlas plans.

## Run locally

### 1. Clone the repository

    git clone https://github.com/riieeya/atlas-travel-planner.git
    cd atlas-travel-planner

### 2. Create a virtual environment

Windows PowerShell:

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1

macOS or Linux:

    python3 -m venv .venv
    source .venv/bin/activate

### 3. Install dependencies

    pip install -r requirements-dev.txt

### 4. Configure the environment

Windows PowerShell:

    Copy-Item .env.example .env

macOS or Linux:

    cp .env.example .env

Add your private SerpApi key to `.env`:

    SERPAPI_API_KEY=your_real_key_here

Never commit the real `.env` file.

### 5. Start Atlas

    uvicorn travel_demo_server:app --host 127.0.0.1 --port 3001 --reload

Open:

    http://127.0.0.1:3001

API documentation is available locally at:

    http://127.0.0.1:3001/api/docs

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `SERPAPI_API_KEY` | Private SerpApi credential required for live searches | None |
| `ATLAS_SEARCH_CACHE_SECONDS` | Search-cache duration | `600` |
| `ATLAS_SEARCHES_PER_MINUTE` | Per-client quota protection | `15` |

## Tests

Run the complete suite:

    pytest -q

Run compilation and JavaScript syntax checks:

    python -m compileall -q .
    node --check assets/app.js

Current verified result:

    18 passed

GitHub Actions installs the declared dependencies and runs tests and Python compilation on pushes to `main` and on pull requests.

## Privacy and security boundaries

- Only submitted travel-search fields are sent to SerpApi.
- API keys remain on the backend.
- Atlas does not request payment details.
- Planning state remains in browser local storage.
- Unexpected API fields are rejected.
- Past dates and invalid round-trip dates are rejected.
- Search calls use timeouts, caching and rate limiting.
- Provider handoffs require explicit confirmation.
- Atlas never accepts an arbitrary provider URL from the browser.
- Search results are snapshots, not reservations.

## Important limitations

- The airport catalogue is a curated starter list, not a complete aviation dataset.
- Flexible-date fares appear only after the user searches those dates.
- Travel times between activities are manually entered estimates.
- Destination suggestions are starter templates, not live recommendations.
- Prices and availability can change between search and provider checkout.
- Plans do not synchronize across devices.

## Roadmap

- Maintained global airport and location dataset
- Bounded fare-calendar comparison
- Activity editing and map-based travel-time estimates
- Planned-versus-actual budget tracking
- Exportable trip summaries
- Accessible end-to-end browser testing
- Official supplier integrations after product and legal validation
- Deeper Hushh integration only after the standalone architecture is validated

## Safety principles

Atlas will not use scraped search results as a direct booking system. A future production booking flow must use provider-hosted checkout or official supplier APIs, reprice before confirmation, prevent duplicate actions and reconcile final provider status.

## Repository

[github.com/riieeya/atlas-travel-planner](https://github.com/riieeya/atlas-travel-planner)
