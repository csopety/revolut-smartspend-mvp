# SmartSpend Premium MVP

SmartSpend is a local Streamlit MVP for a Revolut-style grocery planning feature. It helps a user compare a planned basket before shopping, estimate the budget impact, and simulate saving the difference toward a goal.

The demo is scoped to Budapest II and four supported grocery chains: Lidl, Aldi, SPAR, and Tesco.

## Simulated MVP Disclaimer

All banking, grocery, transaction, savings, route, historical, and pilot KPI data is simulated for a local demo. The app does not connect to real banks, Revolut accounts, payment systems, receipt OCR, retailer APIs, live grocery prices, or real money movement. Recommendations are estimates based on supported simulated data, not guaranteed-cheapest claims.

## Final Feature List

- Premium dark phone-style Streamlit UI with four screens: Home, Plan, History, and Setup.
- SQLite persistence at `data/smartspend_demo.db`.
- Search-first grocery basket builder with English and Hungarian aliases.
- 75+ simulated products and four simulated Budapest II stores.
- Deterministic optimizer with basket price, travel cost, time cost, budget fit, confidence, unavailable items, and ranked results.
- Investor demo scenario that loads settings and basket without finalizing a purchase.
- Closed-loop finalization: store actually visited, custom list name, optional travel monetary cost, optional simulated savings goal, and post-finalization verification.
- Previous grocery lists and favorite grocery lists.
- Simulated savings goals and save-the-difference moment.
- Current-month on-track prediction using current and historical demo data.
- Spending insights charts and simulated pilot KPI dashboard.
- Trust/audit drawer explaining data, formulas, guardrails, and simulation boundaries.
- Optional OpenRouteService walking/car route lookup with safe simulated fallback.
- Agentic-style explanation that explains calculated results only.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Testing

```bash
pytest
python -m py_compile app.py smartspend/*.py
```

The suite covers database seeding, search, basket behavior, optimizer logic, warnings, explanations, routes, transactions, previous lists, favorites, savings goals, and insights.

## Architecture

- `app.py`: Streamlit phone-style UI and screen navigation.
- `smartspend/database.py`: SQLite initialization, migrations, seed data, and profile persistence.
- `smartspend/product_search.py`: deterministic search over names, aliases, prefixes, partials, and tags.
- `smartspend/basket.py`: basket add/edit/remove/clear logic.
- `smartspend/optimizer.py`: rule-based recommendation engine.
- `smartspend/route_service.py`: OpenRouteService walking/car lookup with simulated fallback.
- `smartspend/transactions.py`: purchase finalization, spending update, and previous list persistence.
- `smartspend/favorites.py`: favorite list save/reload/delete.
- `smartspend/savings.py`: simulated savings goals and movements.
- `smartspend/insights.py`: historical spending insights and on-track prediction.
- `smartspend/warnings.py`: deterministic budget warnings.
- `smartspend/agentic_explainer.py`: explanation layer that does not change calculations.
- `tests/`: unit tests for backend behavior and safety rules.

## Product Search

Product discovery is typeahead-first with no category dropdown. Search matches product name, display name, Hungarian name, aliases, prefixes, partial strings, and tags. Demo terms include `cucu` and `ubi` for cucumber, `tej` for milk, `csir` for chicken products, and `trap` for Trappista cheese.

## Optimizer

For each supported store, SmartSpend calculates:

- product basket total
- unavailable required items
- confidence score
- travel monetary cost
- travel-time opportunity cost
- net comparison total
- remaining budget after purchase
- overspend amount
- savings versus usual store
- savings versus most expensive option
- max-travel eligibility
- route source

Optimization modes include cheapest basket, lowest total cost including travel, best budget fit, and balanced recommendation. The algorithm is deterministic and auditable; AI is not used to make rankings.

## Finalization And Budget Rules

Planning a basket does not update spending. Running a recommendation does not update spending. Reloading previous lists or favorites does not update spending.

Only finalizing a simulated purchase updates spent so far. Product basket total always counts toward grocery spending. Travel monetary cost counts only if the user selects it at finalization. Travel-time opportunity cost never counts as real spending.

## Previous Lists And Favorites

Finalized purchases are saved as previous grocery lists. A previous list can be viewed, reloaded for planning, or saved as a favorite. Favorite lists can be saved from the current basket, viewed, reloaded, or deleted. These actions are planning conveniences and do not update spending.

## Savings Goals

The app seeds simulated goals such as Emergency fund, Holiday, and New laptop. If a finalized shop has positive estimated savings versus the usual store, the UI can simulate moving that difference into a selected goal. This is clearly labeled as simulated and does not move real money.

## On-Track Prediction

History → Insights includes “Will I stay on track this month?” It uses current simulated spend, monthly budget, historical average, weekly distribution, and over-budget frequency to produce a deterministic projection, over/under amount, likelihood percentage, and explanation bullets.

## Pilot KPI Dashboard

History → Pilot proof shows simulated adoption, repeat usage, average saving per finalized shop, savings-goal usage uplift, basket estimate variance, and trust/compliance status. Average saving uses local transactions when available and falls back to a seeded demo value otherwise.

## Trust/Audit Drawer

Setup and Pilot proof include a trust/audit drawer with data used, data not used, formulas, guardrails, and the simulated-data disclaimer. It explicitly states there is no real banking connection, Revolut account, payment, retailer API, money movement, or guaranteed-cheapest claim.

## Optional OpenRouteService

The app works without a live route API. If `OPENROUTESERVICE_API_KEY` is available through the environment, `.env`, or Streamlit secrets, the app can use OpenRouteService for walking and car route estimates when enabled in Setup. `ORS_API_KEY` is also supported as a fallback variable name. Public transport remains simulated in this MVP. If no key exists or the API fails, the app falls back to simulated routes. OpenRouteService only affects distance, travel time, and route source.

## AI And Codex Usage

Codex was used to implement the MVP in phases: data and persistence, search and basket logic, route fallback, optimizer, transactions, savings goals, insights, the premium Streamlit UI, tests, and documentation. The app’s recommendation and prediction calculations remain deterministic Python logic. The agentic explanation layer only explains calculated outputs and does not change rankings, prices, spending, or savings.

## Limitations

- Simulated prices may not match real stores.
- Store availability and promotions are invented for demo purposes.
- Route data is simulated unless OpenRouteService is enabled and available for walking or car routes.
- The app has no authentication or production privacy model.
- The app is not financial advice.
- There is no real Revolut integration.
- There is no live retailer, banking, payment, receipt OCR, or account-data integration.
- The UI is an MVP prototype, not a production mobile app.

## Manual Acceptance Checklist

See [docs/acceptance_checklist.md](docs/acceptance_checklist.md) for the final QA checklist.
