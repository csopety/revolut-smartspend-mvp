# Implemented Vs Not Implemented

This table maps the business-plan idea to the implemented MVP scope.

| Business-plan feature | Implemented in MVP | Excluded or future scope |
| --- | --- | --- |
| Pre-purchase grocery planning | Search-first basket builder and store comparison | None |
| Revolut-style experience | Premium dark phone-style Streamlit UI | Native mobile app |
| Budget tracking | Simulated monthly budget, spent amount, remaining budget, and progress | Real bank account balance |
| Store recommendation | Deterministic ranking across Lidl, Aldi, SPAR, and Tesco | Real-time retailer price feeds |
| Product search | Typeahead search with English and Hungarian aliases | Barcode scanning and receipt OCR |
| Basket optimization | Product total, travel cost, time cost, budget fit, savings, confidence, and ranking | Personalized ML ranking |
| Travel estimates | Simulated routes plus optional OpenRouteService walking/car estimates | Real public transport API |
| Starting location | Saved origin address and explicit OpenStreetMap Nominatim geocoding | Background geocoding while typing |
| Finalize purchase | Simulated finalization, transaction lines, previous list, budget update | Real checkout or payment |
| Save the difference | Simulated savings movement to selected goal | Real transfer to a Revolut Pocket |
| Previous grocery lists | View, inspect, reload, and favorite finalized lists | Shared household lists |
| Favorites | Save, reload, view, and delete favorite baskets | Cloud sync |
| Spending insights | Historical charts, store split, weekly pattern, and on-track prediction | Live bank transaction analytics |
| Warnings | Deterministic budget warnings and projected overspend signals | Regulated financial advice |
| Pilot KPI dashboard | Simulated adoption, repeat usage, savings, variance, and trust metrics | Real pilot analytics |
| Trust and audit | Data used, data not used, formulas, guardrails, and disclaimers | Production compliance system |
| AI explanation | Agentic-style explanation of calculated results only | AI changing rankings or moving money |
| Persistence | Local SQLite database | Production database and authentication |
| API security | Environment-variable based optional route key handling | Server-side key vault or deployed secrets manager |

The MVP demonstrates the business concept while keeping all financial behavior simulated and auditable.
