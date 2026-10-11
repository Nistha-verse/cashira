# Cashira

**Cashira** is a cash-flow early-warning dashboard for lenders that serve small merchants, starting with kirana stores. It helps lenders identify merchants whose cash flow may be weakening **before** an EMI becomes overdue.

> **Cashira does not change the loan or EMI. It helps lenders understand merchant cash-flow health earlier and prioritize follow-up.**

## Problem

Lenders that provide credit to small merchants often discover repayment stress only after an EMI is missed. By then, the merchant may already be under cash-flow pressure, and the lender has limited time to intervene.

A merchant’s sales may decline for several weeks, but the lender may not have an easy way to identify that decline early across many merchants.

## Solution

Cashira analyzes merchant sales or transaction history and generates simple cash-flow signals for the lender:

- Sales trend
- Cash-flow health status
- Data coverage
- Risk alerts
- Suggested follow-up action

For example, if a merchant’s sales have declined for two weeks and an EMI is due soon, Cashira flags the merchant as high priority. The lender can then contact the merchant, review the account, or send a reminder before the payment becomes overdue.

Cashira is a **decision-support tool**, not an automated lending system. The lender makes the final decision.

## Product Flow

```text
Merchant transaction / sales data
        ↓
Cashira analytics engine
        ↓
Cash-flow health and risk signals
        ↓
Lender dashboard alerts
        ↓
Lender reviews and takes action
```

## Example

```text
Merchant: Riya Kirana Store

Sales declined 37% over the last two weeks.
EMI due in 5 days.
Cash-flow health: Weak.

Alert:
High priority — contact merchant before EMI due date.
```

The lender can mark the alert as:

- Contacted
- Under review
- False positive
- No action needed

## What Cashira Does Not Do

Cashira does **not**:

- Change a merchant’s EMI.
- Collect payments.
- Approve or reject loans.
- Make automated credit decisions.
- Access real bank, UPI, or Account Aggregator data in this prototype.
- Guarantee that a merchant will not default.
- Replace a bank, NBFC, or regulated lender.

Cashira provides early cash-flow visibility. The lender remains in control of all lending and repayment decisions.

## Hackathon Prototype

This repository contains a hackathon prototype built with **synthetic merchant data**.

The prototype demonstrates:

- A merchant sales dashboard.
- Cash-flow trend analysis.
- A lender dashboard with prioritized merchants.
- Early-warning alerts with explanations.
- A simple lender action workflow.
- Simulated merchant and lender views.

No real financial data, payments, bank integrations, or Account Aggregator connections are used.

## Tech Stack

### Frontend

- Next.js
- React
- Tailwind CSS
- Recharts

### Backend

- FastAPI
- Python
- PostgreSQL / Supabase

### Analytics

- Python
- Pandas
- NumPy

### Optional future extensions

- Prophet for time-series forecasting
- Account Aggregator integration
- UPI or POS data integration
- Blockchain-based audit logging

Blockchain is **not required** for the core product. A normal database with audit logs is sufficient for the MVP.

## Architecture

```text
Merchant data source
        ↓
FastAPI backend
        ↓
PostgreSQL / Supabase database
        ↓
Analytics engine
        ↓
Alert engine
        ↓
Lender dashboard
```

### Components

| Component | Purpose |
|---|---|
| Merchant data source | Provides sales or transaction data; synthetic data in the prototype |
| FastAPI backend | Handles APIs, merchant records, alerts, and dashboard data |
| Database | Stores merchants, sales records, alerts, and lender actions |
| Analytics engine | Calculates sales trend, volatility, data coverage, and cash-flow health |
| Alert engine | Flags merchants with weakening cash flow |
| Lender dashboard | Displays prioritized merchants and alerts |

## Core Logic

The MVP uses transparent rules rather than claiming advanced AI accuracy.

Example alert logic:

```text
If sales declined significantly over the last two weeks
AND the decline is sustained
AND an EMI is due soon,
then create a high-priority alert.
```

The dashboard explains why a merchant was flagged:

```text
Why flagged?
- Sales declined 37% versus previous two weeks
- Sales declined on 12 of the last 14 days
- EMI due in 5 days
- Data coverage: 26 of 30 days
```

## Getting Started

### Prerequisites

- Node.js
- Python 3.10+
- Git

### Install frontend

```bash
cd frontend
npm install
npm run dev
```

### Install backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Environment variables

Create a `.env` file based on `.env.example`.

Do not commit real API keys, database credentials, or secrets.

## Demo Data

The project uses synthetic merchant transaction data to demonstrate the workflow.

Example data format:

```csv
date,merchant_id,sales_amount
2026-10-01,M001,4200
2026-10-02,M001,5100
2026-10-03,M001,3800
2026-10-04,M001,4000
2026-10-05,M001,3500
```

The analytics engine uses this data to calculate:

- Average daily sales
- Sales trend
- Week-over-week change
- Sales volatility
- Data coverage
- Cash-flow health status
- Risk alert level

## Roadmap

### Phase 1 — Hackathon MVP

- Synthetic merchant data
- Sales dashboard
- Cash-flow health indicators
- Lender alert dashboard
- Explainable alerts
- Lender action workflow

### Phase 2 — Pilot

- Consent-based data integration
- Integration with an NBFC or fintech lender
- Real merchant cash-flow monitoring
- Alert feedback and model evaluation

### Phase 3 — Scale

- Improved forecasting and risk signals
- Lender workflow integrations
- Portfolio-level merchant monitoring
- Measurable impact evaluation

## Important Disclaimer

This is a hackathon prototype. It does not provide financial advice, credit decisions, loan approvals, payment processing, or guaranteed default prevention.

All merchant data in this demo is synthetic. A production version would require appropriate consent, privacy, security, compliance, and regulated-lender partnerships.

