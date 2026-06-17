# SmartSpend Architecture

The MVP is intentionally small. It has a Streamlit UI, a simulated data layer, and a pure Python optimizer.

## Modules

```text
app.py
```

Runs the Streamlit interface. It collects user inputs, builds the basket, applies the travel cost per km setting, calls the optimizer, and displays the results.

```text
smartspend/models.py
```

Defines the simple dataclasses used across the app:

- `Product`
- `Store`
- `BasketItem`
- `GroceryDataset`
- `StoreResult`

```text
smartspend/data_generator.py
```

Creates the simulated Budapest II dataset. This includes grocery chains, products, prices, neighborhoods, travel times, and a default basket.

```text
smartspend/optimizer.py
```

Contains the rule-based calculation. It does not know anything about Streamlit, so it can be tested independently.

```text
tests/test_optimizer.py
```

Tests the calculation logic, including basket totals, travel cost, eligibility, budget impact, savings, and rankings.

## Data Flow

```text
Simulated data
  -> Streamlit inputs
  -> basket and adjusted store travel costs
  -> optimizer
  -> ranked store results
  -> Streamlit display
```

## Design Choices

- Streamlit keeps the UI easy to run locally.
- Dataclasses keep the data readable for beginners.
- Simulated data avoids paid APIs and fragile scraping.
- The optimizer is pure Python so it is easy to test.
- The recommendation is rule-based so the evaluator can audit the calculation.

## Boundaries

The MVP does not include persistence, authentication, real transactions, retailer integrations, map routing, or real personal finance data. Those would belong in later product phases, not this school-assignment MVP.
