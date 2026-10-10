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
creates 24 months of daily inflows and outflows for three synthetic merchants,
from October 2024 through September 2026. It validates rows before inserting
them and reports four deliberately malformed/duplicate rows that were skipped.
After seeding, the command prints a per-merchant monthly inflow/outflow/net
table. The SQLite file is `backend/data/cashira.db` and is ignored by git.

The sales generator uses a weekday base near ₹7,000, Saturday near ₹12,000,
and Sunday near ₹8,500 before deterministic noise and seasonal effects. Riya's
normal sales months are close to ₹2.5 lakh. Asha and Kabir use 0.93x and 1.07x
merchant scale factors. Inventory purchases track each day's sales at roughly
80%; monthly supplier payments are ₹2,000–₹4,000 and monthly rent is fixed per
merchant between ₹8,000 and ₹10,000. Month-start effects and a Diwali-season
peak are included. September 2026 is Riya's weak month, with sales reduced by
roughly 35–40% while rent remains unchanged.

The demo loans use 18% annual interest over 24 months. Their principals are
₹1,80,000 for Riya, ₹2,00,000 for Asha, and ₹2,20,000 for Kabir. Standard EMIs
are derived from the shared amortization formula: approximately ₹8,986.34,
₹9,984.82, and ₹10,983.30 respectively. Each configured monthly range is 70%
to 120% of that merchant's standard EMI; reseeding resets the balance to the
principal and carried-forward shortfall to zero.

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

## Optional testnet anchor

The `contracts/` Hardhat project contains the owner-gated `CashiraAnchor`
contract. Its local tests cover an authorized write, an unauthorized failure,
and the emitted event:

```bash
cd contracts
npm install
npm test
```

For Polygon Amoy, copy `contracts/.env.example`, set the RPC URL and a
throwaway testnet key, deploy with `npm run deploy:amoy`, then set the matching
backend `CHAIN_*` variables and `CHAIN_ENABLED=true`. Anchor calls are
best-effort: if disabled or unavailable, recommendations, payments, receipts,
and verification continue to work without an anchor.
