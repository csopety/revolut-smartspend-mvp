# SmartSpend Data Generation

SmartSpend uses synthetic data so the MVP can be run, tested, and graded without external retailer, banking, or payment systems.

## Products

The demo database contains at least 75 grocery products across common food categories. Products include English names, display names, Hungarian aliases, tags, and search-friendly terms.

Examples:

- `cucu` and `ubi` match cucumber.
- `tej` matches milk.
- `csir` matches chicken products.
- `trap` matches Trappista cheese.

## Prices And Availability

Each product has a row for every supported store. A store-price row includes:

- price in HUF when available
- availability flag
- promotion flag

Some products may be intentionally unavailable at a store to demonstrate confidence and availability handling. The optimizer must account for those cases.

## Store Data

The MVP includes four supported Budapest II grocery chains:

- Lidl
- Aldi
- SPAR
- Tesco

Stores include seeded coordinates for route estimates. Store coordinates are stored as latitude and longitude. OpenRouteService requests convert them to `[longitude, latitude]` order.

## Historical Spending

The database seeds at least six months of realistic simulated grocery spending. Snapshots include monthly totals, weekly distribution, store split, highest purchase, and most-used store.

This data powers:

- average monthly grocery spending
- average basket value
- average grocery trips per month
- highest and lowest spending month
- weekly spending pattern
- store split chart
- current-month on-track prediction

## Transactions

Transactions are created only when a user finalizes a simulated purchase. Transaction line items are saved for auditability and for previous-list reloads.

Building a basket, comparing stores, reloading previous lists, and reloading favorites do not create transactions.

## Savings Goals

The seeded goals are simulated examples, such as Emergency fund, Holiday, and New laptop. Estimated positive savings can be shown as a simulated movement toward a selected goal. This is not a real transfer.

## Why Simulation Is Used

Simulation keeps the assignment safe, reproducible, and easy to grade. It avoids:

- real banking data
- real card payments
- real retailer integrations
- scraping
- production privacy requirements
- live price claims

The goal is to demonstrate the product logic and user journey, not to provide real financial or retail advice.
