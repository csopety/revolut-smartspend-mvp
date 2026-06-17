# Revolut SmartSpend MVP

SmartSpend is a small Streamlit MVP for a FinTech school assignment. It shows how a Revolut-style budgeting feature could help a user decide where to buy a grocery basket before spending money.

The demo focuses on Budapest II district and uses simulated grocery prices, travel times, and travel costs. It does not connect to banks, retailers, payment systems, or map APIs.

## What The MVP Does

- Lets the user set a monthly grocery budget and amount already spent.
- Lets the user choose quantities for a small grocery basket.
- Compares 4 simulated grocery chains in Budapest II.
- Calculates basket price, travel cost, effective total cost, remaining budget, and savings against the user's usual store.
- Marks stores as eligible or ineligible based on maximum travel time.
- Recommends the best eligible store.
- Simulates moving savings into a SmartSpend Pocket.

## Install

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## Test

Activate the virtual environment, then run:

```bash
pytest
```

The tests focus on the optimizer logic because the calculation is the core of the MVP.

## Simulated Data

All grocery and travel data is invented for demonstration. The dataset includes:

- 4 chains: Aldi, Lidl, SPAR, and Tesco
- 3 categories: Bakery, Dairy, and Produce
- 6 products with simulated HUF prices
- simulated Budapest II neighborhoods
- simulated travel times
- travel cost calculated from a user-controlled cost per km

This keeps the app presentation-ready without requiring Google Maps, retailer APIs, scraping, or paid services.

## Algorithm

For each store, SmartSpend:

1. Multiplies each selected product price by its quantity.
2. Adds those values to get the basket price.
3. Adds estimated travel cost to get the effective total cost.
4. Checks whether the store is within the user's maximum travel time.
5. Compares the result with the user's usual store.
6. Calculates expected savings and remaining monthly grocery budget.
7. Ranks eligible stores first, then sorts by lowest effective total cost.

The algorithm is rule-based and auditable. AI is not used to make the financial calculation.

## Business-Plan Features Implemented

- Pre-purchase grocery basket comparison
- Budget-aware recommendation
- Travel time and travel cost trade-off
- Store ranking across 4 grocery chains
- Savings estimate versus usual store
- Simulated Revolut-style SmartSpend Pocket
- Clear disclaimer that the data is simulated

## Features Excluded

- real Revolut login
- real bank account connection
- real payments
- real card transactions
- real retailer APIs
- live grocery prices
- Google Maps or paid routing APIs
- web scraping
- personal data storage
- AI-based financial decision-making

These exclusions keep the MVP narrow, stable, ethical, and easy to run locally.

## Project Structure

```text
app.py                    Streamlit user interface
smartspend/models.py      Simple data models
smartspend/data_generator.py
                          Simulated grocery and store data
smartspend/optimizer.py   Rule-based recommendation logic
tests/test_optimizer.py   Unit tests for optimizer behavior
docs/                     Supporting explanation and demo notes
```

## How Codex Was Used

Codex helped build the MVP in small phases:

1. Read the project brief and planned the implementation.
2. Created simulated grocery data and data models.
3. Implemented the transparent optimizer and unit tests.
4. Built the Streamlit interface.
5. Wrote concise documentation for the algorithm, architecture, and demo flow.

The project remains intentionally simple so a beginner can read the code and understand how the recommendation is calculated.
