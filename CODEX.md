# CODEX.md - SmartSpend Premium MVP

This file defines how AI agents should work on the SmartSpend repository. It is written for reproducible development, grading transparency, and safe handling of simulated financial data.

## 1. Project Goal

SmartSpend is a Python Streamlit MVP for a Revolut-style grocery planning feature. It helps a user plan a basket before shopping, compare supported Budapest II stores, estimate budget impact, and simulate saving the difference toward a goal.

The project is a school assignment demo, not a production financial product.

## 2. Current Architecture

- `app.py`: Streamlit UI with phone-style Home, Plan, History, and Setup screens.
- `smartspend/database.py`: local SQLite persistence, migrations, seeded demo data, profile settings, origin coordinates.
- `smartspend/product_search.py`: typeahead search over names, aliases, prefixes, partial matches, and tags.
- `smartspend/basket.py`: basket add, edit, remove, clear, save, and reload behavior.
- `smartspend/optimizer.py`: deterministic store recommendation and cost calculation.
- `smartspend/route_service.py`: simulated routing plus optional OpenRouteService walking/car estimates.
- `smartspend/geocoding.py`: explicit OpenStreetMap Nominatim geocoding for starting locations.
- `smartspend/transactions.py`: simulated finalization, transaction records, previous lists, and spending updates.
- `smartspend/favorites.py`: favorite grocery list save, reload, and delete behavior.
- `smartspend/savings.py`: simulated savings goals and simulated savings movements.
- `smartspend/insights.py`: historical insights, pilot metrics, and current-month on-track prediction.
- `smartspend/warnings.py`: deterministic budget warnings.
- `smartspend/agentic_explainer.py`: explanation text for calculated results only.
- `tests/`: unit and regression tests for the core modules.
- `docs/`: supporting algorithm, architecture, demo, and acceptance material.

The app uses local SQLite at `data/smartspend_demo.db`. Demo data can be rebuilt through `reset_demo_data()`.

## 3. Non-Negotiable Constraints

- Do not rebuild working modules unless a concrete bug or requested feature requires it.
- Do not copy another project wholesale.
- Keep changes small, scoped, and consistent with existing module boundaries.
- Do not introduce a visible category dropdown for product discovery.
- Planning a basket must not update spending.
- Running a recommendation must not update spending.
- Reloading previous lists or favorites must not update spending.
- Only finalizing a simulated purchase may update monthly spent amount.
- Travel-time opportunity cost is for comparison only and never counts as real spending.
- Travel monetary cost counts only when selected during finalization.
- Do not claim guaranteed cheapest results or guaranteed savings.

## 4. Simulated-Data Boundaries

The following are simulated demo data:

- Grocery stores, products, prices, promotions, and availability.
- User budget and current spending.
- Transactions and previous grocery lists.
- Savings goals and savings movements.
- Historical monthly spending and insights.
- Pilot KPI dashboard metrics.
- Public transport route estimates.

SmartSpend does not connect to real banking, Revolut, payment systems, receipt OCR, or retailer APIs. Any savings movement is a simulated status update only.

## 5. Security Rules For API Keys

- Never hardcode API keys.
- Never print API keys.
- Never show API keys or masked API keys in the UI.
- Never include API keys in tests, exceptions, logs, README, CODEX, docs, or commit messages.
- Use `OPENROUTESERVICE_API_KEY` as the primary environment variable.
- `ORS_API_KEY` may be supported as a fallback variable.
- Keep `.env` local and untracked.
- Use `.env.example` only with placeholder values.
- Do not store route API keys in Streamlit session state or SQLite.

## 6. OpenRouteService And OpenStreetMap Rules

OpenStreetMap Nominatim:

- Use only for explicit starting-location geocoding.
- Call only when the user clicks a control such as "Find coordinates".
- Do not geocode on every keystroke, app startup, basket planning, or store comparison.
- Use a valid identifying User-Agent.
- Store successful origin address, latitude, and longitude in `user_profile`.
- If geocoding fails, keep the previous valid origin.
- Nominatim does not require an API key in this MVP.
- Show OpenStreetMap attribution where relevant.

OpenRouteService:

- Use only for walking and car distance/time estimates when enabled and configured.
- Public transport remains simulated in this MVP.
- Use saved origin coordinates and seeded store coordinates.
- Send request coordinates in `[longitude, latitude]` order.
- Return route source `"OpenRouteService"` only after a successful live route response.
- Fall back to route source `"Simulated"` for missing keys, API errors, timeouts, invalid JSON, unsupported modes, or missing route data.
- OpenRouteService may affect only route distance, route time, and route source.
- OpenRouteService must not alter grocery prices, budgets, transactions, savings goals, historical data, or optimizer formulas.

## 7. Deterministic Optimizer Rules

For each store, calculate:

- product total
- unavailable items
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

Rules:

- Walking travel monetary cost is `0 HUF`.
- Public transport and car travel monetary cost is `distance_km * cost_per_km`.
- Travel-time opportunity cost is `travel_time_min * value_of_time_huf_per_min`.
- Net comparison total is product total plus travel monetary cost plus travel-time opportunity cost.
- Stores above max travel time remain visible but cannot win.
- Stores with unavailable required items cannot win unless substitutions are accepted.
- Rankings must be deterministic and explainable.
- Agentic explanation text may explain outputs but must not change calculations, prices, rankings, spending, or savings.

## 8. What AI Agents May And May Not Change

AI agents may:

- Add focused tests for requested behavior.
- Update documentation, demo scripts, and acceptance checklists.
- Fix concrete bugs while preserving existing behavior.
- Add small helper functions that match current architecture.
- Improve UI copy where it clarifies simulated boundaries.

AI agents may not:

- Change optimizer formulas unless explicitly requested.
- Change product prices or availability unless the task asks for data updates.
- Change finalization or budget-safety rules without explicit instruction.
- Remove simulated-data disclaimers.
- Introduce real banking, payment, retailer, or account integrations.
- Expose or request API keys.
- Replace the existing architecture with a different framework.

## 9. Testing Commands

Run tests:

```bash
pytest
```

If `pytest` is not on PATH, use the project virtual environment:

```bash
.venv/bin/pytest
```

Run compile checks:

```bash
python -m py_compile app.py smartspend/*.py
```

Run the app manually:

```bash
streamlit run app.py
```

Implementation work should finish with tests and compile checks unless the user explicitly asks for documentation-only changes.

## 10. Documentation Expectations

Documentation should stay concise, beginner-friendly, and supervisor-ready. It must clearly explain:

- What the MVP does.
- Which data is simulated.
- How to install, run, and test.
- How product search works.
- How the recommendation algorithm works.
- How finalization affects budget.
- How previous lists, favorites, and savings goals work.
- How OpenStreetMap and OpenRouteService are used.
- What is not implemented.
- How Codex/AI was used during development.

Do not include real API keys in any documentation.

## 11. Final Submission Workflow

Before submission:

1. Confirm `README.md`, `CODEX.md`, `.codex/project_brief.md`, and `docs/demo_script.md` describe the final MVP.
2. Run `pytest` or `.venv/bin/pytest`.
3. Run `python -m py_compile app.py smartspend/*.py`.
4. Run `streamlit run app.py` and manually check the Home, Plan, History, and Setup screens.
5. Verify `.env` is untracked and no API key appears in documentation or tests.
6. Confirm the app states that financial data and savings movements are simulated.
7. Record the demo video using the final README/demo script flow.
