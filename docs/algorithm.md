# SmartSpend Algorithm

SmartSpend uses deterministic calculations to compare grocery stores. AI is not used to rank stores, change prices, move money, or make financial decisions.

## Inputs

- Basket products and quantities.
- Store-level product prices, availability, and promotion flags.
- Monthly budget and amount already spent.
- Usual store.
- Max travel time.
- Travel mode.
- Travel cost per km.
- Value of time per minute.
- Route distance, route time, and route source.
- Whether substitutions are accepted.
- Optimization mode.

## Basket Price

For each store:

```text
product_total = sum(product_price_at_store * quantity)
```

Unavailable required items are tracked separately. If a required item is unavailable and substitutions are not accepted, that store cannot win.

## Travel Monetary Cost

Walking has no monetary travel cost:

```text
walking_travel_monetary_cost = 0
```

Car and public transport use the configured cost per km:

```text
travel_monetary_cost = distance_km * travel_cost_per_km
```

Public transport distance/time is simulated in this MVP.

## Travel-Time Opportunity Cost

Time cost is shown for comparison, not as real spending:

```text
travel_time_cost = travel_time_min * value_of_time_huf_per_min
```

This cost never updates monthly spent amount.

## Net Comparison Total

The comparison total is:

```text
net_total_cost = product_total + travel_monetary_cost + travel_time_cost
```

This is used to compare stores. It is not the same as final grocery spending.

## Budget Fit

Budget impact is calculated from product cost plus any selected real travel monetary cost during finalization:

```text
remaining_budget_after_purchase = monthly_budget - spent_so_far - counted_purchase_amount
overspend_amount = max(0, counted_purchase_amount + spent_so_far - monthly_budget)
```

During planning, the app estimates this impact without updating the database.

## Savings

Savings versus usual store:

```text
savings_vs_usual_store = usual_store_net_total - store_net_total
```

Savings versus most expensive option:

```text
savings_vs_most_expensive_store = most_expensive_net_total - store_net_total
```

Savings are estimates based on simulated data. They are not guaranteed.

## Confidence

Confidence is based on whether required items are available and whether the store has complete price coverage for the basket. Stores with missing required items receive lower confidence and cannot win unless substitutions are accepted.

## Ranking

The optimizer keeps every store visible, then ranks deterministically. The winning store depends on the selected optimization mode:

- Cheapest basket: prioritizes lowest product total.
- Lowest total cost including travel: prioritizes lowest net comparison total.
- Best budget fit: prioritizes remaining within budget.
- Balanced recommendation: balances product total, travel, availability, confidence, budget fit, and eligibility.

Global ranking rules:

- Stores outside max travel time remain visible but cannot win.
- Stores with unavailable required items cannot win unless substitutions are accepted.
- Ties are resolved deterministically using stable store data.
- Explanation text must use optimizer outputs only.

## Finalization Rule

Planning and comparison do not update spending. Only finalizing a simulated purchase updates the monthly spent amount, saves transaction lines, creates a previous list, and clears the current basket.
