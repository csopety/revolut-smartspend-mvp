# Manual Acceptance Checklist

Use this checklist after running:

```bash
pytest
python -m py_compile app.py smartspend/*.py
streamlit run app.py
```

## App Launch

- [ ] App opens locally without traceback.
- [ ] UI appears as a dark phone-style frame on desktop.
- [ ] Navigation shows Home, Plan, History, and Setup.
- [ ] Simulated MVP disclaimer is visible or clearly represented.

## Home

- [ ] Budget hero shows remaining budget, spent so far, and progress.
- [ ] Priority warning or on-track summary appears.
- [ ] Before / During / After journey strip is visible.
- [ ] Savings goals preview is visible.
- [ ] Investor demo scenario button loads settings and basket without creating a transaction or savings movement.

## Plan

- [ ] Product discovery uses typeahead search and no visible category dropdown.
- [ ] `cucu` and `ubi` return cucumber first.
- [ ] `tej` returns milk first.
- [ ] `csir` returns chicken products.
- [ ] `trap` returns Trappista cheese first.
- [ ] Adding, editing, removing, and clearing basket items works.
- [ ] Planning a basket does not update spent so far.
- [ ] Comparing stores does not update spent so far.
- [ ] Consent disabled prevents recommendation.
- [ ] Recommendation card shows estimated recommendation, totals, savings, and confidence.
- [ ] Ranked alternatives remain visible.
- [ ] Why-not-other-stores panel explains each non-winner using calculated outputs.
- [ ] Calculation receipt shows product total, travel monetary cost, travel-time cost, net total, usual-store total, savings, and remaining budget.

## Finalization

- [ ] Store actually visited selector is available.
- [ ] Custom list name is available.
- [ ] Travel monetary cost checkbox is available.
- [ ] Optional savings goal selector appears when positive savings exists.
- [ ] Finalizing creates a transaction and previous list.
- [ ] Finalizing clears the current basket.
- [ ] Product basket total updates spent so far.
- [ ] Travel monetary cost updates spent only when selected.
- [ ] Travel-time opportunity cost never updates spending.
- [ ] Post-finalization verification card shows finalized total, usual-store estimate, verified saving, budget-counted amount, remaining budget, and selected savings goal when used.
- [ ] Verification copy clearly states simulated only, no payment, no OCR, and no real transfer.

## History

- [ ] Purchases tab lists finalized lists.
- [ ] Reloading a previous list does not update spending or create a transaction.
- [ ] Previous list can be added to favorites.
- [ ] Favorites tab can save, view, reload, and delete favorites.
- [ ] Reloading a favorite does not update spending or create a transaction.
- [ ] Insights tab shows current-month prediction with status, projected spend, budget, over/under amount, likelihood, and explanation bullets.
- [ ] Charts render with dark styling.
- [ ] Pilot proof tab shows simulated pilot KPIs.
- [ ] Average saving per finalized shop appears and uses local transactions when available.

## Setup

- [ ] Budget/profile settings can be saved and persist after refresh.
- [ ] Origin/address field defaults to Széll Kálmán tér, Budapest II.
- [ ] Travel settings, optimization mode, consent, and Google Maps option are visible.
- [ ] Trust/audit drawer includes data used, data not used, formulas, guardrails, and simulated-data disclaimer.
- [ ] Drawer states no real banking connection, Revolut account, payment, retailer API, money movement, or guaranteed-cheapest claim.
- [ ] Reset demo data restores the deterministic demo state.

## Route Fallback

- [ ] App works with no `GOOGLE_MAPS_API_KEY`.
- [ ] If Google Maps is enabled without a key or fails, route source falls back to Simulated.
- [ ] Google Maps, when configured, only affects distance, travel time, and route source.

## Safety Language

- [ ] UI uses estimated/simulated language.
- [ ] UI avoids guaranteed-cheapest claims.
- [ ] UI does not imply real payment, real banking, real receipt OCR, or real money transfer.
- [ ] Agentic explanation explains calculations only and does not change rankings or money values.
