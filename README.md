# SmartSpend Premium MVP

SmartSpend helps a shopper plan a grocery basket before buying by comparing supported Budapest II stores, estimating budget impact, and simulating saving the difference toward a goal.

## What SmartSpend Is

SmartSpend is a Streamlit fintech MVP for grocery decision support. It lets a user build a basket, compare four simulated Budapest II grocery stores, review the estimated total cost including travel, finalize a simulated purchase, and track how that purchase affects a monthly grocery budget.

## Simulated MVP Disclaimer

This project is an educational demo. Grocery prices, budgets, transactions, savings goals, historical spending, pilot metrics, and success messages are simulated. The app does not connect to a bank, Revolut account, retailer API, payment provider, or real money movement system.

## Main Features

- Premium dark, phone-style Streamlit interface with Home, Plan, History, and Setup screens.
- Search-first grocery basket builder with English and Hungarian product aliases.
- Store comparison for Lidl, Aldi, SPAR, and Tesco using simulated Budapest II data.
- Recommendation cards, ranked alternatives, “why not other stores?” explanations, and calculation receipts.
- Budget tracker with deterministic warnings and current-month on-track prediction.
- Simulated purchase finalization, previous grocery lists, favorite lists, and savings goals.
- Spending insights, Plotly charts, simulated pilot KPI dashboard, and trust/audit drawer.
- Optional live walking/car route estimates through OpenRouteService.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running The App

```bash
streamlit run app.py
```

The app creates and uses a local SQLite demo database at `data/smartspend_demo.db`.

## Testing

```bash
pytest
python -m py_compile app.py smartspend/*.py
```

The tests validate database seeding, product search, basket behavior, route fallbacks, optimizer calculations, warnings, insights, favorites, transactions, and budget-safety rules.

## Required Dependencies

The project dependencies are listed in `requirements.txt`:

- `streamlit`
- `pandas`
- `plotly`
- `requests`
- `python-dotenv`
- `pytest`

## Optional OpenRouteService Setup

Live route estimates are optional. To enable OpenRouteService for walking and car routes, copy the example file and replace the placeholder value:

```bash
cp .env.example .env
```

`.env.example` uses this placeholder environment variable:

```bash
OPENROUTESERVICE_API_KEY=your_openrouteservice_key_here
```

Keep `.env` local. OpenStreetMap Nominatim does not require an API key in this MVP.

## Product Search

Product discovery uses typeahead search, not a category dropdown. Search matches product names, display names, aliases, prefixes, partial strings, and tags. The seeded data includes Hungarian-friendly terms such as `cucu` and `ubi` for cucumber, `tej` for milk, `csir` for chicken products, and `trap` for Trappista cheese.

## Store Recommendation Algorithm

For each store, SmartSpend calculates product total, unavailable items, confidence score, travel monetary cost, travel-time opportunity cost, net comparison total, remaining budget after purchase, overspend amount, savings versus the usual store, savings versus the most expensive option, max-travel eligibility, and route source.

The available optimization modes are cheapest basket, lowest total cost including travel, best budget fit, and balanced recommendation. Stores outside the max travel time or missing required items remain visible but are prevented from winning unless the relevant option allows it.

## Budget And Finalization Rules

Building a basket does not update spending. Running a comparison does not update spending. Only finalizing a simulated grocery purchase updates the monthly spent amount.

The product basket total always counts toward grocery spending. Travel monetary cost counts only when selected during finalization. Travel-time opportunity cost is shown for comparison but never counts as real spending. Finalization validates availability, saves the transaction and line items, stores the grocery list as a previous list, and clears the current basket.

## Previous Lists And Favorites

Finalized grocery lists can be viewed, inspected, reloaded into the current basket, and saved as favorites. Favorite lists can be named, viewed, reloaded, and deleted. Reloading previous lists or favorites does not update spending and does not create a transaction.

## Savings Goals Simulation

The app includes simulated savings goals such as Emergency fund, Holiday, and New laptop. If a finalized shop has a positive estimated saving, SmartSpend can show a simulated “save the difference” movement toward a selected goal. This is a demo-only status update, not a transfer of real money.

## On-Track Prediction

The History screen includes a deterministic “Will I stay on track this month?” card. It uses current spend, monthly budget, seeded historical averages, weekly distribution, and over-budget frequency to estimate projected month-end spend, over/under budget amount, likelihood percentage, severity, and explanation bullets. It does not use AI.

## Trust, Audit, And Simulation Boundaries

The trust/audit drawer explains the data used, data not used, formulas, and guardrails. Grocery prices, budgets, purchases, savings goals, historical data, and pilot metrics are simulated. OpenStreetMap Nominatim may convert a typed starting location into coordinates only when the user clicks “Find coordinates.” OpenRouteService may estimate walking/car distance and travel time when enabled. Public transport remains simulated.

SmartSpend does not claim a guaranteed cheapest basket or guaranteed savings.

## Software Architecture

- `app.py` contains the Streamlit UI and screen flow.
- `smartspend/database.py` initializes SQLite, runs safe migrations, and seeds demo data.
- `smartspend/product_search.py` handles product matching and ranking.
- `smartspend/basket.py` manages basket operations.
- `smartspend/optimizer.py` calculates store recommendations.
- `smartspend/route_service.py` handles simulated routing and optional OpenRouteService routing.
- `smartspend/geocoding.py` handles explicit OpenStreetMap Nominatim geocoding.
- `smartspend/transactions.py`, `favorites.py`, and `savings.py` handle simulated finalization, lists, favorites, and goals.
- `smartspend/insights.py`, `warnings.py`, and `agentic_explainer.py` provide analytics, deterministic warnings, and explanation text.
- `tests/` contains validation and regression tests.

## Synthetic Data

The SQLite demo database seeds four Budapest II store records, at least 75 products, product aliases in English and Hungarian, store-level price and availability rows for every product-store pair, savings goals, user profile settings, and at least six months of historical spending snapshots. The reset button restores the demo dataset.

## AI/Codex Usage

Codex was used as an implementation assistant to plan phases, edit Python modules, build tests, improve documentation, and run verification commands. The app logic itself is deterministic; AI is not used to make live financial decisions inside the MVP.

## Limitations And Not Implemented

- No real banking integration.
- No real Revolut account connection.
- No real payment or checkout.
- No real retailer inventory or receipt OCR.
- No real public transport routing.
- No automatic background geocoding while typing.
- No production authentication, deployment, or privacy controls.
- No guarantee that a selected store is cheapest or that savings will occur in the real world.

## License And Copyright

No separate open-source license file is included. Copyright remains with the project author unless a license is added.