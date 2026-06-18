# 3-Minute SmartSpend Demo Script

## 0:00-0:20 — Open With The Problem

Run:

```bash
streamlit run app.py
```

Say:

SmartSpend is a simulated Revolut-style grocery planning MVP. Instead of only tracking spending after purchase, it helps a user compare a basket before shopping and understand the budget impact.

Point out the disclaimer: all prices, banking behavior, transactions, savings, routes, history, and pilot KPIs are simulated. There is no real Revolut account, banking connection, payment, receipt OCR, retailer API, or real money movement.

## 0:20-0:45 — Home Screen

Show the phone-style Home screen:

- remaining grocery budget
- spent so far
- progress bar
- on-track or warning summary
- Before / During / After journey strip
- savings goals preview

Say:

The flow is intentionally closed loop: before shopping, plan; during shopping, compare stores; after shopping, finalize a simulated purchase and verify the estimated saving.

Click **Load investor demo scenario**. Explain that it loads realistic settings and a basket only. It does not finalize a purchase, create a transaction, or update a savings goal.

## 0:45-1:35 — Plan Screen

On Plan, show the typeahead search. Search for one of:

- `cucu`
- `ubi`
- `tej`
- `csir`
- `trap`

Explain that discovery is search-first with English and Hungarian aliases and no category dropdown.

Click **Compare supported stores**. Show:

- recommendation card
- ranked store alternatives
- route source
- confidence
- unavailable items
- net total

Say:

The optimizer is deterministic. It compares product total, travel monetary cost, travel-time opportunity cost, budget impact, unavailable items, route source, and max travel time. It does not use AI to decide the ranking.

Open **Why not other stores?** and explain that each reason comes from optimizer outputs only: higher product price, higher net total, outside travel limit, unavailable items, or lower confidence.

Open **Calculation receipt** and show product total, travel monetary cost, travel-time opportunity cost, net total, usual-store net total, savings, and remaining budget.

## 1:35-2:15 — Finalize And Save Difference

In finalization:

- choose the store actually visited
- keep or change the custom list name
- decide whether travel monetary cost counts toward budget
- choose an optional savings goal if positive savings exists
- click **Finalize simulated purchase**

Say:

Planning and comparison do not update spending. Only finalization updates simulated spent so far. Travel-time cost never counts as real spending, and travel monetary cost counts only if selected.

Show the post-finalization success card:

- finalized basket total
- usual-store estimate
- estimated verified saving
- amount counted toward budget
- remaining budget
- selected savings goal movement, if used

Say:

This is the save-the-difference moment. It is simulated only: no payment, no receipt OCR, and no real transfer.

## 2:15-2:45 — History And Insights

Open History.

In **Purchases**, show the finalized previous list and explain that reloading it is a planning action only.

In **Favorites**, explain that favorites can be saved, reloaded, and deleted without affecting spending.

In **Insights**, show “Will I stay on track this month?”:

- status
- projected month-end spend
- budget
- projected over/under amount
- likelihood
- explanation bullets

Say:

This prediction is deterministic and explainable. It uses current simulated spend, historical average, weekly distribution, and over-budget frequency. It does not use AI.

## 2:45-3:00 — Pilot Proof And Trust

Open **Pilot proof** and show the simulated KPI dashboard:

- adoption rate
- repeat usage
- average saving per finalized shop
- savings-goal usage uplift
- basket estimate variance
- trust/compliance status

Open the **Trust and audit drawer**.

Close with:

SmartSpend demonstrates a pre-purchase budgeting loop: plan the basket, compare supported stores, finalize a simulated purchase, verify estimated savings, and optionally simulate saving the difference. The MVP is transparent, deterministic, and intentionally bounded to simulated data.
