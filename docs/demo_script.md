# Demo Script

Use this short flow to present the SmartSpend MVP.

## 1. Open The App

Run:

```bash
streamlit run app.py
```

Explain that SmartSpend is a pre-purchase grocery optimizer. It helps the user decide where to shop before spending money.

## 2. Show The Disclaimer

Point out that all prices, distances, and travel times are simulated for a local MVP. There is no real banking, payment, maps, scraping, or retailer connection.

## 3. Set The Budget

In the sidebar:

- set the monthly grocery budget
- set the amount already spent

Explain that the app uses these values to estimate whether the basket still fits the user's monthly grocery budget.

## 4. Choose Trip Preferences

In the sidebar:

- choose the usual store
- adjust maximum travel time
- adjust travel cost per km

Explain that SmartSpend compares stores based on both product prices and the cost of getting there.

## 5. Build The Basket

Change a few product quantities in Bakery, Dairy, and Produce.

Explain that the app compares the same basket across all stores.

## 6. Show The Recommendation

Highlight:

- recommended store
- basket price
- travel cost
- effective total cost
- expected savings
- remaining budget

Explain that effective total cost is basket price plus travel cost.

## 7. Show Ranked Alternatives

Scroll to the ranked table. Explain that stores outside the maximum travel time are marked ineligible and ranked below eligible stores.

## 8. Simulate The Pocket

Click `Move savings to SmartSpend Pocket` if the recommendation saves money versus the usual store.

Explain that this is a simulated Revolut-style feature. It demonstrates the business idea without moving real money.

## 9. Close With Scope

Say that the MVP proves the core idea:

> SmartSpend moves budgeting from passive tracking after purchase to active guidance before purchase.

Then mention that future production versions would need real integrations, compliance review, accurate price feeds, map routing, and privacy-safe account data handling.
