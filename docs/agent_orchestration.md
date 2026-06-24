# Agent Orchestration

This project used Codex as an implementation assistant under explicit human direction.

## How Codex Was Used

Codex was given phased tasks instead of one broad rebuild. Each phase focused on a specific part of the MVP:

- SQLite data and persistence
- product search, basket logic, and route fallback
- optimizer, warnings, and explanation text
- finalization, previous lists, favorites, and savings goals
- premium Streamlit UI
- insights, pilot KPIs, and trust/audit
- OpenRouteService and OpenStreetMap support
- final QA and documentation

Codex read the current codebase before editing, changed scoped files, added tests for new behavior, and ran verification commands after implementation phases.

## What Codex Was Allowed To Modify

Codex could modify:

- Python modules in `smartspend/`
- `app.py`
- tests in `tests/`
- documentation in `README.md`, `CODEX.md`, `.codex/`, and `docs/`

Codex was expected to keep existing module boundaries, preserve working behavior, and avoid unnecessary rewrites.

## What Codex Was Not Allowed To Modify Without Direction

Codex was not allowed to:

- expose or hardcode API keys
- change product prices unless requested
- change optimizer formulas unless requested
- change finalization or budget-safety rules unless requested
- add real banking, payment, retailer, or Revolut integrations
- remove simulated-data disclaimers
- claim guaranteed cheapest results or guaranteed savings

## Human Review

The human user defined the business requirements, phase boundaries, acceptance criteria, and final demo priorities. The human also tested the app manually through the GitHub repository and fed comments back into Codex as follow-up instructions.

Human review was used to check:

- UI flow and presentation quality
- whether the recommendation was understandable
- whether simulated boundaries were clear
- whether route and origin behavior matched expectations
- whether finalization changed spending only at the correct moment

## Testing

Codex was instructed to run:

```bash
pytest
python -m py_compile app.py smartspend/*.py
```

When `pytest` was not available on PATH, the project virtual environment command was used:

```bash
.venv/bin/pytest
```

Tests cover persistence, search, basket behavior, routing, geocoding, optimizer results, warnings, transactions, favorites, savings, and insights.

## Rejected Suggestions

Several ideas were intentionally rejected or avoided:

- Real bank or Revolut integration, because the MVP is simulated.
- Real payment or checkout, because it is outside assignment scope.
- Retailer scraping, because data must remain reproducible and safe.
- AI-driven ranking, because the recommendation must be deterministic and auditable.
- Auto-geocoding while typing, because geocoding should happen only on explicit user action.
- Large rewrites, because incremental changes were safer and easier to test.

## Version Control Approach

GitHub was used as the shared source of truth. Work was developed iteratively with commits, pushes, pulls, and branches as needed. One teammate focused on Codex-driven implementation and prompt refinement, while the other tested the app, reviewed behavior, and helped decide which comments should become follow-up Codex instructions.
