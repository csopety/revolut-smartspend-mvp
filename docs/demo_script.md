# 10-Minute SmartSpend Demo Script

This outline is designed for a supervisor-facing video presentation.

## 0:00-0:45 - Opening And Value Proposition

Show the app starting with:

```bash
streamlit run app.py
```

Say:

SmartSpend is a simulated Revolut-style grocery planning MVP. It helps a user plan a basket before shopping, compare supported stores, estimate budget impact, and simulate saving the difference toward a goal.

Point out that this is an educational MVP with simulated grocery, budget, transaction, savings, and historical data.

## 0:45-1:45 - Home Screen

Show:

- monthly budget
- spent so far
- remaining budget
- progress bar
- warning or on-track summary
- Before / During / After journey strip
- savings goals preview

Explain that the product is built around a closed loop: plan, compare, finalize, verify, and save.

## 1:45-2:45 - Investor Demo Scenario

Click the investor demo scenario button if available.

Explain:

- it loads realistic settings and a sample basket
- it does not finalize a purchase
- it does not create a transaction
- it does not update a savings goal

This demonstrates the app quickly without changing spending state.

## 2:45-4:15 - Product Search And Basket

Go to Plan.

Search for examples:

- `cucu` or `ubi`
- `tej`
- `csir`
- `trap`

Explain that search uses names, display names, aliases, prefixes, partial strings, and tags. There is no category dropdown.

Add or adjust products in the basket. Mention that building a basket is planning only and does not affect monthly spending.

## 4:15-5:45 - Store Recommendation

Run the store comparison.

Show:

- recommended store
- ranked alternatives
- product total
- travel monetary cost
- travel-time opportunity cost
- net comparison total
- confidence
- route source
- unavailable items, if any

Explain that the optimizer is deterministic. It does not use AI to choose the winner.

## 5:45-6:45 - Why Not Other Stores And Receipt

Open the "why not other stores" panel.

Explain that each sentence uses optimizer outputs only, such as higher net total, higher product price, outside travel limit, unavailable items, or lower confidence.

Open the calculation receipt and show:

- basket total
- travel monetary cost
- travel-time opportunity cost
- usual-store net total
- savings versus usual store
- savings versus most expensive option
- remaining budget after purchase

## 6:45-7:45 - Finalize Simulated Purchase

In the finalization section:

- select the store actually visited
- enter a custom list name
- decide whether to include travel monetary cost
- select a savings goal if positive estimated savings exist
- finalize the simulated purchase

Explain:

- planning does not update spending
- comparison does not update spending
- only finalization updates spending
- travel-time cost never counts as real spending
- travel monetary cost counts only if selected

Show the success moment and verification numbers.

## 7:45-8:45 - History, Favorites, And Insights

Go to History.

Show:

- finalized previous lists
- favorite lists
- list reload behavior
- spending insight charts
- current-month on-track prediction

Explain that reloading previous lists or favorites is a planning action only. It does not create a transaction or update spending.

## 8:45-9:30 - Pilot Proof And Trust

Show the simulated pilot KPI dashboard:

- adoption rate
- repeat usage
- average saving per finalized shop
- savings-goal usage uplift
- basket estimate variance
- trust/compliance status

Open the trust/audit drawer and explain:

- what data is used
- what data is not used
- formulas
- guardrails
- simulated-data boundaries

## 9:30-10:00 - Setup, Routing, And Closing

Go to Setup.

Show:

- monthly budget and profile settings
- starting location
- OpenStreetMap Nominatim geocoding button
- optional OpenRouteService live routing
- reset demo data

Close with:

SmartSpend demonstrates a transparent pre-purchase grocery budgeting loop. The MVP is deterministic, testable, and intentionally limited to simulated financial behavior.
