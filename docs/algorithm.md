# SmartSpend Algorithm

SmartSpend uses a transparent rule-based algorithm. It does not use AI to decide which store is best.

## Inputs

- monthly grocery budget
- amount already spent this month
- basket item quantities
- usual store
- maximum travel time
- travel cost per km
- simulated product prices and travel times

## Calculation

For each store:

1. Calculate basket price:

   ```text
   basket price = sum(product price * quantity)
   ```

2. Calculate travel cost:

   ```text
   travel cost = estimated distance * travel cost per km
   ```

3. Calculate effective total cost:

   ```text
   effective total cost = basket price + travel cost
   ```

4. Check travel eligibility:

   ```text
   eligible = store travel time <= user's maximum travel time
   ```

5. Calculate budget impact:

   ```text
   remaining budget = monthly budget - already spent - effective total cost
   ```

6. Calculate savings versus the usual store:

   ```text
   savings = usual store effective total cost - this store effective total cost
   ```

## Ranking

Stores are ranked using this order:

1. eligible stores first
2. lower effective total cost first
3. shorter travel time as a tie-breaker
4. store name as a final stable tie-breaker

This means a very cheap store can still appear below other options if it is outside the user's maximum travel time.

## Output

The optimizer returns one result per store with:

- rank
- basket price
- travel cost
- effective total cost
- remaining budget
- savings versus usual store
- travel eligibility
- budget fit

The Streamlit app shows the first eligible ranked store as the recommendation.
