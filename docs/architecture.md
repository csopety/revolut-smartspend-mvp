# SmartSpend Architecture

SmartSpend is a local Streamlit MVP with a modular Python backend, SQLite persistence, deterministic recommendation logic, simulated grocery data, and optional live route estimates.

## Frontend

`app.py` contains the Streamlit interface. The UI is organized as a phone-style app with four screens:

- Home: budget status, progress, warnings, journey strip, and savings preview.
- Plan: product search, basket builder, store comparison, recommendation, receipt, and finalization.
- History: purchases, previous lists, favorites, spending insights, and pilot proof.
- Setup: profile settings, origin address, travel settings, consent, live routing, reset, and trust/audit.

The frontend does not own business rules. It gathers inputs, calls backend functions, and displays calculated results.

## Backend Modules

- `smartspend/database.py`: SQLite setup, migrations, seeded data, user profile, store/product data, current basket, and reset support.
- `smartspend/product_search.py`: typeahead product matching over product names, display names, aliases, prefixes, partial strings, and tags.
- `smartspend/basket.py`: add, edit, remove, clear, save, and reload basket actions.
- `smartspend/optimizer.py`: deterministic recommendation logic and ranking.
- `smartspend/route_service.py`: simulated routes and optional OpenRouteService walking/car routes.
- `smartspend/geocoding.py`: explicit OpenStreetMap Nominatim geocoding for starting locations.
- `smartspend/transactions.py`: simulated purchase finalization, transaction lines, previous lists, and spending updates.
- `smartspend/favorites.py`: favorite list save, reload, view, and delete behavior.
- `smartspend/savings.py`: simulated savings goals and simulated movements.
- `smartspend/insights.py`: spending insights, pilot metrics, and on-track prediction.
- `smartspend/warnings.py`: deterministic budget warnings.
- `smartspend/agentic_explainer.py`: explanation text for calculated optimizer results.

## Database And Persistence

The app stores demo data in local SQLite at `data/smartspend_demo.db`.

Main persisted entities:

- `user_profile`
- `stores`
- `products`
- `store_prices`
- `historical_monthly_spending`
- `current_basket_items`
- `transactions`
- `transaction_line_items`
- `previous_lists`
- `previous_list_items`
- `favorite_lists`
- `favorite_list_items`
- `savings_goals`
- `savings_movements`

Migrations are additive and safe for existing local demo databases. `reset_demo_data()` clears and reseeds the demo state.

## Route APIs

The MVP works without any external route API.

OpenStreetMap Nominatim is used only when the user explicitly clicks "Find coordinates" for a starting location. It converts a typed address into latitude and longitude. It does not require an API key.

OpenRouteService is optional. If a placeholder environment variable is configured locally, walking and car routes may use live distance and travel-time estimates. Public transport remains simulated. If live routing is unavailable, fails, or is disabled, the app falls back to simulated routes.

Live route APIs affect only distance, travel time, and route source. Grocery prices, budgets, transactions, savings goals, and historical data remain simulated.

## Optimizer

The optimizer receives basket items, user settings, store data, prices, and route results. It calculates product total, availability, confidence, travel monetary cost, travel-time opportunity cost, net comparison total, budget impact, savings, and eligibility.

The optimizer is deterministic. It does not use AI to decide rankings.

## Streamlit UI Boundaries

The UI must not change spending during planning or comparison. Only finalization may update simulated spending. Reloading a previous list or favorite list is a planning action and must not create a transaction.

## High-Level Flow

```text
User input
  -> Streamlit UI
  -> SQLite-backed profile, basket, stores, products, prices
  -> optional route/geocoding helpers
  -> deterministic optimizer
  -> ranked recommendation and explanation
  -> optional simulated finalization
  -> persisted transaction, previous list, and updated budget state
```
