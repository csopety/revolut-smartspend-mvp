# CODEX.md — SmartSpend MVP Agent Instructions

## Project goal
Build a Python Streamlit MVP for Revolut SmartSpend, a pre-purchase grocery basket optimizer for Budapest II district.

## Final implementation direction

Important context:
The current project is our own SmartSpend codebase. A separate reference project was reviewed only as a feature checklist. Do not copy or overwrite our project with the reference project.

The current codebase already includes:
- SQLite persistence
- product search
- basket logic
- store recommendation optimizer
- transaction finalization backend
- previous lists
- favorites
- savings goals
- route fallback
- spending insights
- deterministic warnings
- agentic explanation

The final implementation should improve and complete the current project, not rebuild it.

## Features still required

Implement these missing or incomplete features:

1. Phone-style navigation:
   - Home
   - Plan or Basket
   - History
   - Setup

2. Premium dark Revolut-style UI:
   - dark navy/black background
   - electric purple and blue gradients
   - glassmorphism cards
   - phone frame on desktop
   - white typography
   - muted grey secondary text
   - glowing recommendation cards

3. Persistent setup/profile settings:
   - save monthly budget
   - save usual store
   - save max travel time
   - save travel monetary cost per km
   - save origin/address if implemented
   - preserve values after refresh/restart

4. Guided Before / During / After journey:
   - Before shopping: budget risk and planning
   - During shopping: basket comparison
   - After shopping: finalize, verify savings, save difference

5. Investor demo mode:
   - one-click demo scenario
   - realistic budget, spent so far, usual store, travel assumptions, basket
   - must not finalize a transaction automatically

6. Stronger finalization UX:
   - store actually visited
   - custom list name
   - include travel monetary cost checkbox
   - optional savings goal if positive savings exist
   - clear post-finalization success state

7. Simulated savings verification:
   - compare finalized basket with usual-store estimate
   - show estimated verified saving
   - clearly label as simulated
   - no OCR, no payment, no real money movement

8. Recommendation transparency:
   - why this store won
   - why not other stores
   - calculation receipt
   - confidence and route labels

9. Current-month on-track prediction:
   - History / Insights card
   - projected month-end spend
   - on-track likelihood
   - explanation bullets
   - deterministic and explainable

10. Richer historical insights:
   - weekly pattern
   - store split
   - over/under budget
   - selected month details

11. Pilot KPI dashboard:
   - simulated adoption
   - repeat usage
   - average saving per shop
   - savings-goal usage uplift
   - basket estimate variance
   - trust/compliance status

12. Trust and audit drawer:
   - data used
   - data not used
   - formulas
   - guardrails
   - simulation boundaries

## Non-negotiable rules

- Do not copy the reference project wholesale.
- Do not rebuild working modules unless a concrete bug requires it.
- Preserve tests.
- Budget changes only after finalization.
- Reloading previous lists or favorites must not change budget.
- Travel-time cost never counts as real spending.
- Travel monetary cost counts only if explicitly enabled.
- All banking, savings, route, historical, and grocery data are simulated.
- No real Revolut integration.
- No real banking connection.
- No real payment.
- No real receipt OCR.
- No guaranteed-cheapest claims.
- AI/agentic explanation must not change calculations.

## Business context
SmartSpend helps users make better grocery spending decisions before purchase. The MVP compares stores based on basket price, travel time, travel cost, remaining budget, and expected savings.

## Business-plan logic
The original concept is a Revolut budgeting extension that moves personal finance from passive post-transaction tracking to active pre-purchase optimization. The MVP should show this through a grocery basket comparison and savings recommendation.

## Non-negotiable constraints
- Use Python.
- Use Streamlit for the user interface.
- Use simulated data by default.
- The MVP must run locally with: streamlit run app.py
- The test suite must run with: pytest
- Do not require Google Maps or any paid API for the basic demo.
- Do not build real banking, real payment, real scraping, or real personal-data integrations.
- Keep the recommendation algorithm rule-based, transparent, and auditable.
- AI may help explain trade-offs, but AI must not make the financial calculation.
- Keep the MVP narrow, stable, and presentation-ready.

## MVP scope
- Location: Budapest II district.
- Grocery chains: 4 chains.
- Product categories: 3 basic food categories.
- User input: budget, already spent amount, basket, max travel time, usual store.
- Output: recommended store, ranked alternatives, expected savings, explanation, and simulated “save the difference” flow.

## Core features
1. User sets a monthly grocery budget.
2. User enters a grocery basket.
3. App compares 4 grocery chains.
4. Algorithm calculates basket price, travel cost, effective total cost, savings, and budget fit.
5. App recommends the best store.
6. App explains why that store was selected.
7. App simulates moving the savings into a Revolut-style Pocket.

## Core algorithm idea
For each store:
1. Calculate basket price.
2. Add estimated travel cost.
3. Check whether travel time is within the user's maximum travel time.
4. Compare effective total cost against the user's usual store.
5. Estimate savings.
6. Show budget impact.
7. Rank stores using transparent rule-based scoring.

## Quality standards
- Simple and readable code.
- Clear function names.
- Type hints where useful.
- Unit tests for optimizer logic.
- Beginner-friendly README.
- No hidden magic.
- No overclaiming of price accuracy.
- Include a disclaimer that all grocery prices and store distances are simulated for MVP purposes.

## Development workflow
- Work in small phases.
- After each phase, run pytest.
- After each stable change, commit to Git.
- Before major changes, explain the plan first.
- Do not rewrite the whole project without permission.

## V2 Premium MVP upgrade

We are upgrading the simple SmartSpend demo into a high-quality MVP.

The app must include:
- Typeahead product search with no visible category dropdown.
- At least 75 simulated products with English and Hungarian aliases.
- Four stores: Lidl, Aldi, SPAR, Tesco.
- Deterministic recommendation algorithm.
- SQLite persistence.
- Finalized grocery transactions.
- Previous grocery lists.
- Favorite grocery lists.
- Simulated savings goals.
- Historical spending insights with charts.
- Deterministic warning messages.
- Optional Google Maps route integration with safe fallback.
- Agentic-style explanation layer that explains calculated results but never changes calculations.

Important rules:
- Budget changes only after finalizing a purchase.
- Planning a basket must not update spending.
- Reloading previous lists must not update spending.
- Reloading favorites must not update spending.
- Travel-time cost never counts as real spending.
- Travel monetary cost counts only if explicitly enabled.
- All banking, savings, transactions, prices, route data, and historical data are simulated.
- The app must work without external APIs.
- Do not hardcode API keys.
- Do not connect to real banks, Revolut, payment systems, real retailer APIs, or real user financial accounts.