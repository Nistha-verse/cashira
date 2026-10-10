# Cashira backend

Cashira is a backend-only hackathon prototype for a regulated lender's future
decision-support integration. It recommends a **monthly** EMI from consented,
synthetic kirana-store records. It does not lend, move money, contact banks,
send SMS, or run an LLM.

## Setup

```bash
cd backend
python -m venv .venv             # already present in the supplied repo
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed
uvicorn app.main:app --reload
```

The seed command is deterministic (`--seed 42` by default), idempotent, and
creates 12 months of daily inflows and outflows for three synthetic merchants.
It validates rows before inserting them and reports deliberately malformed rows
that were skipped. The SQLite file is `backend/data/cashira.db` and is ignored
by git.

OpenAPI is available at `http://localhost:8000/docs`; the endpoint contract and
example JSON are in [`../docs/API.md`](../docs/API.md).

## Test

```bash
cd backend
pytest -q
```

## Design notes

- `services/engine.py` is a pure deterministic rule. It scales between the
  configured minimum and maximum using the ratio of the next 30-day forecast
  net to the trailing monthly net average. The forecast never directly chooses
  an EMI.
- `services/forecast.py` exposes both `ProphetForecaster` and a deterministic
  trailing-eight-week same-weekday baseline. Prophet is opt-in with
  `USE_PROPHET=true`; any unavailable, short, or failed Prophet run falls back
  to the baseline and records `forecast_method`.
- The baseline forecast is an estimate, not a guarantee. Daily records and
  forecasts are inputs only; repayment events are monthly.
- Explanations are selected from templates in `services/explain.py`, so the
  wording can be translated later without changing the rule.

## Assumptions and limitations

- All merchants, records, forecasts, payments, and OTPs are synthetic. The OTP
  is fixed by `.env` and authentication is a demo session token, not real
  identity verification.
- The loan balance uses a fixed-rate amortization placeholder. Interest is
  applied once per simulated monthly payment; a payment below the standard EMI
  accumulates a carried-forward shortfall. A lower EMI does not imply a lower
  total owed.
- Cashira is advisory decision support, not a lender. It does not connect to
  real banks, UPI, money movement, SMS, or any production credit service.
- Prophet outputs are forecasts with ranges rather than guarantees. The
  fallback is intentionally simple and transparent.
- The optional testnet anchor, when enabled in the later build, is an
  illustration only and must use a throwaway testnet key. Merchant identity,
  records, and balances do not belong on-chain.
