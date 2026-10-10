# Cashira API

Every successful response includes `prototype: true` and a synthetic-data
notice. Amounts are illustrative units and repayment is monthly.

## `POST /auth/request-otp`

Request: `{"phone":"+919900000001"}`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","phone":"+919900000001","otp_requested":true,"demo_code":"123456","message":"A simulated OTP is ready for this prototype."}
```

## `POST /auth/verify-otp`

Request: `{"phone":"+919900000001","code":"123456"}`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","verified":true,"session_token":"<sha256-demo-token>","phone":"+919900000001"}
```

## `GET /merchant/me`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","merchant":{"id":1,"name":"Riya's Corner Store","business_type":"kirana store","city":"Bengaluru","consented_at":"2024-01-01T00:00:00"}}
```

## `GET /merchant/transactions?from=2024-01-01&to=2024-01-03`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","records":[{"id":1,"date":"2024-01-01","direction":"inflow","category":"shop sales","amount":35000.0,"description":"Synthetic daily shop sales"}],"count":1,"data_quality":{"invalid_rows_stored":0,"note":"Invalid input rows are skipped during seeding."}}
```

## `GET /merchant/summary`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","months":[{"month":"2024-11","inflow":1000000.0,"outflow":700000.0,"net":300000.0,"change_vs_trailing_average":12000.0}],"latest_month":{"month":"2024-11","inflow":1000000.0,"outflow":700000.0,"net":300000.0,"change_vs_trailing_average":12000.0},"trailing_average_net":288000.0}
```

## `GET /merchant/forecast`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","method":"baseline","horizon_days":30,"expected_net":310000.0,"lower_net":220000.0,"upper_net":400000.0,"daily":[{"date":"2025-01-01","expected":10000.0,"lower":7000.0,"upper":13000.0}],"disclaimer":"Forecast is an estimate, not a guarantee."}
```

## `GET /loan`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","loan":{"id":1,"principal":180000.0,"annual_rate_percent":18.0,"tenure_months":24,"min_emi":6290.44,"max_emi":10783.61,"standard_emi":8986.34,"due_day":5,"current_balance":180000.0,"carried_forward_shortfall":0.0,"payments":[],"amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}}
```

## `GET /loan/recommendation`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","recommendation_id":1,"current_emi":8633.38,"range":{"min":6290.44,"max":10783.61},"standard_emi":8986.34,"reasons":[{"code":"cash_flow_position","message":"The recommended EMI reflects the forecast next-month net cash flow compared with the trailing average.","forecast_net":382250.37,"trailing_average_net":375802.86,"ratio":1.0172},{"code":"steady_capacity","message":"Recent cash flow is close to its trailing average."}],"explanation":"We used a transparent cash-flow rule: the 30-day forecast is compared with your trailing monthly net average. The recent outlook is close to usual, so the payment stays near the middle of your agreed range.","forecast_method":"baseline","rule_version":"cashira-emi-v1","forecast":{"expected_net":382250.37,"lower_net":284601.87,"upper_net":479898.69},"summary":{"trailing_average_net":375802.86,"latest_month":{"month":"2024-12","inflow":1111999.84,"outflow":735567.25,"net":376432.59,"change_vs_trailing_average":629.73}},"amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}
```

## `POST /loan/pay`

Request: `{"amount":9000,"payment_date":"2025-01-05"}`. Omit `amount` to use
the current recommendation.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","payment_id":1,"payment":{"amount":9000.0,"payment_date":"2025-01-05","interest_component":2700.0,"principal_component":6300.0,"balance_after":173700.0,"carried_forward_shortfall":0.0},"message":"Simulated monthly payment recorded.","amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}
```

## `GET /records/{id}/receipt`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","record":{"id":1,"record_type":"recommendation","record":{},"hash":"0x...","signature":"0x...","prev_hash":null,"rule_version":"cashira-emi-v1","created_at":"2025-01-01T00:00:00"}}
```

## `POST /records/verify`

Request: `{"record_id":1}` or a receipt payload with `record`, `hash`, and
`signature`.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","verified":true,"hash_valid":true,"signature_valid":true,"chain_valid":true,"anchored":false,"message":"This record is verified: its contents, signature, and chain link match."}
```

## `GET /health`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","status":"ok","service":"cashira-backend"}
```
