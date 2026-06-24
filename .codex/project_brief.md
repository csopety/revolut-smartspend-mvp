# SmartSpend Project Brief

This brief explains the business context, final MVP scope, and how Codex was orchestrated during development.

## 1. SmartSpend Business Context

SmartSpend is a proposed Revolut-style grocery planning feature. The user plans a shop before buying, compares supported grocery stores, sees the likely budget impact, and can simulate saving the difference toward a goal.

The assignment goal is to demonstrate a credible fintech MVP: clear user value, explainable calculations, strong simulation boundaries, and a polished product demo. The MVP is not a real banking product and does not move money.

## 2. MVP User Journey

The final demo journey is:

1. Home: user sees monthly grocery budget, spent amount, remaining budget, warning or on-track prediction, and savings goals preview.
2. Plan: user searches for products, builds a basket, compares stores, reviews the recommendation, checks alternatives, and reads the calculation receipt.
3. Finalize: user chooses the store actually visited, decides whether travel monetary cost counts, optionally selects a savings goal, and finalizes a simulated purchase.
4. Verify: user sees finalized basket total, usual-store estimate, estimated saving, amount counted toward budget, and remaining budget.
5. History: user reviews previous lists, favorites, insights, and simulated pilot proof.
6. Setup: user manages budget/profile settings, starting location, travel settings, live routing option, consent, reset, and trust/audit information.

The intended story is: Plan -> Compare -> Finalize -> Verify -> Save.

## 3. Implemented Features

- Premium dark, phone-style Streamlit UI.
- Home, Plan, History, and Setup screens.
- Local SQLite persistence at `data/smartspend_demo.db`.
- Simulated Budapest II grocery data for Lidl, Aldi, SPAR, and Tesco.
- 75+ products with English and Hungarian aliases.
- Typeahead product search with support for terms such as `cucu`, `ubi`, `tej`, `csir`, and `trap`.
- Basket add, edit, remove, clear, save, and reload behavior.
- Deterministic recommendation engine with ranked store results.
- Travel monetary cost, travel-time opportunity cost, budget impact, and savings calculations.
- Optional OpenRouteService walking/car route estimates.
- Explicit OpenStreetMap Nominatim starting-location geocoding.
- Simulated transaction finalization with previous-list creation.
- Favorite grocery lists.
- Simulated savings goals and save-the-difference success moment.
- Deterministic warnings and current-month on-track prediction.
- Spending insights, charts, and simulated pilot KPI dashboard.
- Trust/audit drawer explaining data used, data not used, formulas, and guardrails.
- Unit and regression tests for core behavior.

## 4. Not Implemented Features

- Real Revolut account connection.
- Real bank account connection.
- Real payment, checkout, or card transaction processing.
- Real money transfer into savings pockets.
- Real retailer inventory, pricing API, scraping, or receipt OCR.
- Real public transport route integration.
- Production authentication, deployment, privacy controls, or multi-user account system.
- Guarantee that a store is cheapest or that real-world savings will occur.

These exclusions are intentional because the project is a simulated MVP for demonstrating the concept, algorithm, and user flow.

## 5. How Codex Was Orchestrated

Codex was used as a phased development assistant. Work was split into small implementation phases:

- data, SQLite persistence, and seed data
- product search, basket logic, and routes
- optimizer, warnings, and explanation layer
- transactions, previous lists, favorites, and savings goals
- premium Streamlit UI integration
- predictive insights, pilot KPIs, and trust/audit
- OpenRouteService and OpenStreetMap support
- final QA, documentation, and demo materials

Each phase had explicit constraints, such as not rebuilding working modules, not changing optimizer formulas unless requested, preserving finalization safety rules, and keeping all financial behavior simulated.

## 6. Why Suggestions Were Accepted Or Rejected

Accepted suggestions were those that improved the MVP while staying inside the assignment scope:

- SQLite was accepted because it gives visible persistence without requiring external infrastructure.
- Deterministic rules were accepted because the recommendation must be explainable for grading.
- Typeahead search was accepted because it fits the grocery-planning flow better than category browsing.
- Optional OpenRouteService was accepted because it improves realism while preserving fallback behavior.
- OpenStreetMap Nominatim was accepted only for explicit user-triggered geocoding.
- The dark phone-style UI was accepted because it supports the Revolut-style demo narrative.

Rejected or avoided suggestions included:

- Real banking or payment integration, because it is outside MVP scope and unsafe for a school demo.
- Retailer scraping or live price claims, because the assignment uses synthetic data.
- Auto-geocoding on every keystroke, because it is unnecessary and unreliable.
- AI-generated financial recommendations, because the app should remain deterministic and auditable.
- Large rewrites, because the current modular codebase already worked and incremental changes were safer.

## 7. How Human Verification Was Used

Human verification guided the final shape of the MVP. The human user:

- Defined the business-plan features and phase boundaries.
- Approved which features belonged in the final demo.
- Supplied exact store coordinates for live routing updates.
- Checked the app manually with `streamlit run app.py`.
- Confirmed environment setup behavior, including local `.env` handling.
- Directed documentation updates for supervisor readiness.
- Required tests and compile checks after implementation phases.

Codex assisted with implementation and verification commands, but final product direction and acceptance criteria came from the human user.
