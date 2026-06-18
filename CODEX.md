# CODEX.md — SmartSpend Premium MVP

## Project Goal

SmartSpend is a Python Streamlit MVP for a Revolut-style pre-purchase grocery planning feature in Budapest II. It compares a planned grocery basket across supported stores, estimates budget impact before purchase, and simulates saving the difference toward a goal.

## OpenRouteService live routing integration

The final MVP may use OpenRouteService for live route distance and travel-time estimates.

Important:
- Never hardcode API keys.
- Never print API keys.
- Never commit `.env` or `.streamlit/secrets.toml`.
- Use environment variable `OPENROUTESERVICE_API_KEY`.
- Optional fallback names may include `ORS_API_KEY`.
- Use `.env.example` only with placeholder values.
- If no API key exists, use simulated route fallback.
- If API call fails, use simulated route fallback.
- If travel mode is public transport, use simulated route fallback unless a real public-transport API is implemented.
- OpenRouteService may be used for walking and car routes.
- OpenRouteService must affect only distance, travel time, and route source.
- OpenRouteService must not affect grocery prices, budgets, transactions, historical data, savings goals, or optimizer formulas except through route distance/time inputs.

## Final Architecture

- `app.py`: premium dark phone-style Streamlit UI with Home, Plan, History, and Setup screens.
- `smartspend/database.py`: local SQLite persistence at `data/smartspend_demo.db`, additive migrations, seeded demo data, profile update support.
- `smartspend/product_search.py`: search over product names, display names, aliases, prefixes, partial strings, and tags.
- `smartspend/basket.py`: basket add/edit/remove/clear behavior.
- `smartspend/route_service.py`: optional OpenRouteService walking/car route lookup with simulated fallback.
- `smartspend/optimizer.py`: deterministic store recommendation logic.
- `smartspend/transactions.py`: simulated purchase finalization, transaction lines, previous lists, and spending updates.
- `smartspend/favorites.py`: favorite list save/reload/delete.
- `smartspend/savings.py`: simulated savings goals and simulated movements.
- `smartspend/insights.py`: historical insights and current-month on-track prediction.
- `smartspend/warnings.py`: deterministic budget warnings.
- `smartspend/agentic_explainer.py`: explanation layer that explains calculated results only.
- `tests/`: unit tests for persistence, search, basket, optimizer, routes, transactions, favorites, savings, warnings, insights, and explanations.
- `docs/`: algorithm, architecture, demo script, and acceptance checklist.

## Final Feature Set

- Premium dark Revolut-style phone UI.
- Four-screen navigation: Home, Plan, History, Setup.
- Simulated Budapest II data for Lidl, Aldi, SPAR, and Tesco.
- 75+ products with English and Hungarian aliases.
- Typeahead product search with no visible category dropdown.
- Persistent setup/profile settings: budget, usual store, max travel time, travel cost per km, and origin/address.
- Investor demo scenario that loads realistic settings and basket without finalizing a purchase.
- Recommendation engine with product total, unavailable items, confidence, travel monetary cost, travel-time cost, net total, budget impact, savings, max-travel eligibility, and route source.
- Optimization modes: cheapest basket, lowest total cost including travel, best budget fit, and balanced recommendation.
- “Why not other stores?” explanation using optimizer outputs only.
- Calculation receipt with all major cost components.
- Simulated purchase finalization with store actually visited, custom list name, travel cost checkbox, optional savings goal, and verification receipt.
- Previous grocery lists and favorite lists.
- Simulated savings goals and save-the-difference success moment.
- Current-month on-track prediction in History → Insights.
- Historical charts for monthly budget, weekly pattern, and store split.
- Simulated pilot KPI dashboard.
- Trust/audit drawer with data used, data not used, formulas, guardrails, and simulation boundaries.
- Optional OpenRouteService support through `OPENROUTESERVICE_API_KEY`, with `ORS_API_KEY` fallback and safe simulated fallback.

## Non-Negotiable Rules

- Do not copy another reference project wholesale.
- Do not rebuild working modules unless a concrete bug requires it.
- Preserve existing tests and add focused tests for new behavior.
- Budget changes only after finalizing a simulated purchase.
- Planning a basket must not update spending.
- Running a recommendation must not update spending.
- Reloading previous lists or favorites must not update spending.
- Product basket total always counts toward spending after finalization.
- Travel monetary cost counts only when explicitly selected at finalization.
- Travel-time opportunity cost never counts as real spending.
- Savings movements are simulated only and must not be represented as real money movement.
- No real Revolut integration.
- No real banking connection.
- No real payment.
- No real receipt OCR.
- No real retailer API or scraping.
- No guaranteed-cheapest claims.
- AI/agentic explanation must not change calculations, prices, rankings, spending, or savings.

## Data And Persistence

The app uses local SQLite persistence stored at `data/smartspend_demo.db`. Demo data is created by `ensure_demo_database()` and can be reset with `reset_demo_data()`.

Core tables include:

- `user_profile`
- `savings_goals`
- `products`
- `stores`
- `store_prices`
- `historical_monthly_spending`
- `transactions`
- `transaction_line_items`
- `previous_lists`
- `previous_list_items`
- `favorite_lists`
- `favorite_list_items`
- `current_basket_items`
- `savings_movements`

SQLite migrations must be additive and safe for existing demo databases.

## Search Requirements

Product search must support names, display names, Hungarian names, aliases, prefixes, partial strings, and tags. Required demo terms include:

- `cucu` and `ubi` for cucumber
- `tej` for milk
- `csir` for chicken products
- `trap` for Trappista cheese

No category dropdown should be introduced.

## Optimizer Rules

For each store, calculate product total, unavailable items, confidence, travel monetary cost, travel-time opportunity cost, net comparison total, remaining budget after purchase, overspend amount, savings versus usual store, savings versus most expensive option, max-travel eligibility, route source, and rank.

Stores above max travel remain visible but cannot win. Stores with unavailable required items cannot win unless substitutions are explicitly accepted. All calculations must be deterministic and explainable.

## Finalization Rules

Only `finalize_purchase()` updates simulated spent so far. Finalization saves a transaction, transaction line items, a previous list, and clears the current basket. Previous-list reloads and favorite reloads are planning actions only and must not create transactions or update budget.

## Insights And Trust

Current-month prediction must be deterministic and use current spend, budget, historical average, weekly distribution, and over-budget frequency. Pilot KPIs are simulated, with average saving per finalized shop calculated from local transactions when available.

Trust/audit copy must clearly state what data is used, what data is not used, formulas, guardrails, and the simulated-data disclaimer.

## Commands

Run the app:

```bash
streamlit run app.py
```

Run tests:

```bash
pytest
```

Compile check:

```bash
python -m py_compile app.py smartspend/*.py
```

## Development Workflow

Work in small phases. Read the current code before editing. Prefer existing module boundaries and helper functions. Keep changes scoped, preserve tests, and run `pytest` plus `py_compile` after implementation work.
