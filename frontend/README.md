# Cashira frontend

Cashira is a frontend-only Next.js App Router prototype for lender review of synthetic small-merchant cash-flow data. The API is the source of truth. The app does not modify the backend.

## Setup

Requirements: Node 20 or newer and a running Cashira API.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The app runs at `http://localhost:3000`. The API defaults to `http://localhost:8000`; override it with `NEXT_PUBLIC_API_URL` in `.env.local`. `.env*` files are ignored except for the committed `.env.example`.

Required scripts:

```bash
npm run dev
npm run build
npm run lint
npm run test
```

Demo credentials are shown on the login screen. The backend demo OTP is `123456`; the lender demo phone is `+919900000099` and the merchant demo phone is `+919900000001`.

## Route map

| Route | Purpose |
| --- | --- |
| `/` | Public landing page and role entry points |
| `/lender/login` | Simulated lender OTP login |
| `/lender` | Portfolio, status counts, filters, and re-evaluation |
| `/lender/merchants/[id]` | Merchant trend, signals, estimate, repayment, alerts, and actions |
| `/lender/alerts` | Filterable alert inbox |
| `/lender/demo` | Visible demo-only scenario controls |
| `/merchant/login` | Simulated shopkeeper OTP login and language picker |
| `/merchant` | Consent, localized messages, and monthly sales |
| `/merchant/messages` | Localized lender reminders |
| `/merchant/sales` | Date-filtered transaction records and sales chart |
| `/records` | Record-ID lookup and records collected in this browser session |
| `/records/[id]` | Receipt details, verification, download, and changed-record test |

## Role flows

1. Enter from `/`, choose lender or shopkeeper, request the simulated OTP, and enter the shown demo code.
2. The role and bearer token are stored in `sessionStorage` under `cashira.session`.
3. Lender routes are guarded to lender sessions. Merchant routes are guarded to merchant sessions; a wrong role is redirected to its own home route.
4. Lender actions are explicitly simulated and link to a receipt ID when the create-action response provides one.
5. Merchant language is stored in `localStorage` as `cashira.language`; merchant API calls include `?lang=` and localized message text comes from the API response.
6. A revoked merchant is rendered only as **Consent withdrawn**. The lender list and detail view do not render its financial fields.

## Design tokens and implementation

- Forest `#01472e`, Sage `#ccd5ae`, Olive `#e9edc9`, Cream `#fefae0`, Moss `#a3b18a`, Amber `#f2d58a`, and Brick `#9b2c1d` are CSS variables in `app/globals.css` and mapped into Tailwind.
- Anton is used for display headings; Inter for lender UI; Noto Sans Devanagari and Noto Sans Bengali are applied to translated merchant views.
- Shared primitives include `Money`, `DateValue`, `StatusChip`, the typed client in `lib/api.ts`, and the role/session contexts.
- Charts use Recharts with legends, plain-word axes, rupee formatting, and text summaries. Status chips always contain an icon and a label.
- A fixed SVG noise overlay, organic rounded cards, underline inputs, responsive cards, reduced-motion handling, and the persistent prototype banner are part of the global shell.

## Backend mismatches

These are handled in the UI without backend changes:

1. `GET /records` does not exist. `/records` therefore provides a record-ID input and links to action/demo record IDs collected in this session.
2. `POST /merchant/consent/revoke` creates a signed `consent_change` record internally but does not return its `audit_record_id`. The merchant UI shows the withdrawn state and cannot invent a receipt link.
3. `GET /lender/merchants/{id}/actions` does not return `audit_record_id`. The action list links records returned by a create response in this session; older list rows explain that the record ID was not included.
4. There is no action-message preview endpoint. The action form states this and displays the API-rendered message after a simulated action is recorded.
5. The alert response includes `merchant_id` and `signal_id`, but not merchant name or a signal title. The inbox joins merchant names from the portfolio and uses the exact signal ID when a title is unavailable.
6. Merchant messages have no date field. The messages screen displays “Date not provided” rather than inventing one.
7. `lang` is formally declared by OpenAPI on `/merchant/messages`, but not on `/merchant/me`, `/merchant/consent`, `/merchant/consent/revoke`, `/merchant/summary`, or `/merchant/transactions`. The frontend sends `?lang=` on all merchant API calls as requested; FastAPI ignores unsupported query parameters on those endpoints.
8. Lender detail returns the balance inside `emi_suggestion.loan.current_balance`, not inside `repayment`; the detail view uses that exact returned field for the repayment balance.
9. The backend receipt contains protected fields needed by `/records/verify`. The UI does not expose raw transaction-chain values; it shows plain-language matches/does-not-match results and retains the receipt JSON for download/verification.
10. In the current backend, `/merchant/consent/revoke` commits the revocation and then can return HTTP 500 because its response references an undefined local `merchant`. The frontend re-reads consent after a failed revoke and shows **Consent withdrawn** when the committed status is `revoked`; the backend remains unchanged.

## Assumptions

- The browser session is the simplest record index because the API has no list endpoint.
- Merchant sales default to the most recent thirty available days when no dates are selected.
- A missing nullable API field renders as an em dash or friendly empty state; no fallback financial value is fabricated.
