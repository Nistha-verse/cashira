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
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","merchant":{"id":1,"name":"Riya's Corner Store","business_type":"kirana store","city":"Bengaluru","consented_at":"2024-10-01T00:00:00"}}
```

## `GET /merchant/transactions?from=2024-10-01&to=2024-10-01`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","records":[{"id":1,"date":"2024-10-01","direction":"inflow","category":"shop sales","amount":7749.63,"description":"Synthetic daily shop sales"},{"id":2,"date":"2024-10-01","direction":"outflow","category":"inventory purchases","amount":6166.2,"description":"Synthetic supplier inventory purchase"},{"id":3,"date":"2024-10-01","direction":"outflow","category":"rent","amount":9000.0,"description":"Synthetic monthly rent"}],"count":3,"data_quality":{"invalid_rows_stored":0,"note":"Invalid input rows are skipped during seeding."}}
```

## `GET /merchant/summary`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","months":[{"month":"2026-09","inflow":146076.14,"outflow":127787.62,"net":18288.52,"change_vs_trailing_average":-19360.42}],"latest_month":{"month":"2026-09","inflow":146076.14,"outflow":127787.62,"net":18288.52,"change_vs_trailing_average":-19360.42},"trailing_average_net":37648.94,"valid":true}
```

## `GET /merchant/forecast`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","method":"baseline","horizon_days":30,"expected_net":25007.13,"lower_net":-28372.6,"upper_net":78386.9,"daily":[{"date":"2026-10-01","expected":673.05,"lower":-1106.28,"upper":2452.37}],"disclaimer":"Forecast is an estimate, not a guarantee."}
```

## `GET /loan`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","loan":{"id":1,"principal":180000.0,"annual_rate_percent":18.0,"tenure_months":24,"min_emi":6290.44,"max_emi":10783.61,"standard_emi":8986.34,"due_day":5,"current_balance":180000.0,"carried_forward_shortfall":0.0,"payments":[],"amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}}
```

## `GET /loan/recommendation`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","recommendation_id":1,"current_emi":6651.12,"range":{"min":6290.44,"max":10783.61},"standard_emi":8986.34,"reasons":[{"code":"cash_flow_position","message":"The recommended EMI reflects the forecast next-month net cash flow compared with the trailing average.","forecast_net":25007.13,"trailing_average_net":37648.94,"ratio":0.6642},{"code":"lower_capacity","message":"Recent cash flow suggests keeping the monthly payment closer to the lower end of the agreed range."}],"explanation":"We used a transparent cash-flow rule: the 30-day forecast is compared with your trailing monthly net average. The recent outlook is softer than usual, so the payment is nearer the lower end of your agreed range.","forecast_method":"baseline","rule_version":"cashira-emi-v1","forecast":{"expected_net":25007.13,"lower_net":-28372.6,"upper_net":78386.9},"summary":{"trailing_average_net":37648.94,"latest_month":{"month":"2026-09","inflow":146076.14,"outflow":127787.62,"net":18288.52,"change_vs_trailing_average":-19360.42}},"amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}
```

## `POST /loan/pay`

Request: `{"amount":9000,"payment_date":"2026-10-05"}`. Omit `amount` to use
the current recommendation.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","payment_id":1,"payment":{"amount":9000.0,"payment_date":"2026-10-05","interest_component":2700.0,"principal_component":6300.0,"balance_after":173700.0,"carried_forward_shortfall":0.0},"message":"Simulated monthly payment recorded.","amortization":"Prototype assumption: fixed-rate amortization is used; any shortfall versus the standard monthly EMI carries forward and does not reduce the total owed.","repayment_frequency":"monthly"}
```

## `GET /records/{id}/receipt`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.","record":{"id":1,"record_type":"recommendation","record":{},"hash":"0x...","signature":"0x...","prev_hash":null,"rule_version":"cashira-emi-v1","created_at":"2026-10-01T00:00:00"}}
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

## Lender authentication

### `POST /auth/lender/request-otp`

Request: `{"phone":"+919900000099"}`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","phone":"+919900000099","otp_requested":true,"demo_code":"123456","role":"lender","message":"A simulated lender OTP is ready for this prototype."}
```

### `POST /auth/lender/verify-otp`

Request: `{"phone":"+919900000099","code":"123456"}`. Use the returned
Bearer token for `/lender/*` endpoints.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","verified":true,"session_token":"cashira.<encoded>.<signature>","role":"lender","phone":"+919900000099","lender_id":1}
```

## `GET /merchant/consent`

Requires a merchant Bearer token.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","consent":{"scope":"transaction history","status":"active","granted_at":"2024-10-01T00:00:00","expires_at":"2027-09-30T00:00:00","revoked_at":null,"message_key":"consent.transaction_history","params":{},"text":"I agree to share my transaction history for cash-flow review."}}
```

## `POST /merchant/consent/revoke`

Requires a merchant Bearer token. It creates a signed `consent_change` record.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","consent":{"status":"revoked","scope":"transaction history"},"message_key":"consent.revoked","params":{},"message":"Consent withdrawn. New lender review is stopped."}
```

## `POST /lender/evaluate?as_of=2026-09-30`

Requires a lender Bearer token. Evaluation is idempotent.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","as_of":"2026-09-30","merchants_evaluated":11,"alerts":11}
```

## `GET /lender/portfolio?as_of=2026-09-30`

Revoked or expired merchants contain only a consent-withdrawn stub.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","as_of":"2026-09-30","counts":{"green":7,"amber":1,"red":3,"consent withdrawn":1},"merchants":[{"id":8,"name":"Lucknow Basket","city":"Lucknow","status":"red","four_week_sales_change":-0.2211,"emi_coverage":2.4392,"open_alerts":3,"next_due":"2026-10-05","days_overdue":0,"consent_status":"active"},{"id":12,"name":"Noida Daily Mart","city":"Noida","status":"consent withdrawn","consent_status":"revoked"}]}
```

## `GET /lender/merchants/{id}?as_of=2026-09-30&lang=hi`

The detail response contains the 26-week Monday-Sunday series, monthly summary,
signals and rendered reasons, a ranged forecast estimate, repayment history,
read-only EMI suggestion, consent, and alerts.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","merchant":{"id":8,"name":"Lucknow Basket","city":"Lucknow","preferred_language":"hi","scenario":"falling for three weeks"},"status":"red","consent":{"status":"active","scope":"transaction history"},"signals":{"status":"red","signals":[{"id":"S1","severity":"red","reason_key":"signals.s1","params":{"decline_weeks":3,"cumulative_drop":0.3805},"text":"बिक्री 3 हफ्तों से कम हुई है। कुल कमी 38.1% है।","rule_version":"cashira-s1-v1"}],"what_to_look_at_first":["S1","S2","S6"]},"forecast":{"label":"estimate, not a guarantee","method":"baseline","expected_net":25522.8,"lower_net":-24143.28,"upper_net":75188.88},"emi_suggestion":{"label":"suggestion for lender review; Cashira does not change any EMI"},"alerts":[{"id":3,"signal_id":"S1","severity":"red","status":"new","message_key":"alerts.s1","text":"बिक्री की गिरती दिशा देखें।"}]}
```

## `GET /lender/alerts?status=new&severity=red&lang=en`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","alerts":[{"id":3,"merchant_id":8,"signal_id":"S1","severity":"red","week_key":"2026-09-21_2026-09-27","status":"new","message_key":"alerts.s1","params":{"decline_weeks":3,"cumulative_drop":0.3805},"text":"Look at the falling sales trend.","rule_version":"cashira-s1-v1"}]}
```

## `POST /lender/alerts/{id}/acknowledge` and `/dismiss`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","alert_id":3,"status":"acknowledged"}
```

## `POST /lender/merchants/{id}/actions`

Request: `{"type":"reminder","note":"Please review","lang":"bn"}`. No
message is sent; the action is stored and signed.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","action_id":1,"type":"reminder","message_key":"reminders.payment","params":{"name":"Mitali Kirana","amount":8986.34},"language":"bn","text":"নমস্কার Mitali Kirana। দয়া করে ₹8,986.34 টাকার পরের EMI দেখুন। এটি একটি সিমুলেটেড রিমাইন্ডার।","sent":false,"audit_record_id":5}
```

## `GET /lender/merchants/{id}/actions`

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","actions":[{"id":1,"type":"reminder","note":"Please review","message_key":"reminders.payment","params":{"name":"Mitali Kirana","amount":8986.34},"language":"bn","text":"নমস্কার Mitali Kirana। দয়া করে ₹8,986.34 টাকার পরের EMI দেখুন। এটি একটি সিমুলেটেড রিমাইন্ডার।"}]}
```

## `GET /merchant/messages?lang=bn`

Requires the merchant token and returns stored reminders rendered in the
merchant’s language or the explicit language override.

```json
{"prototype":true,"notice":"Prototype only: all data is synthetic and simulated; Cashira is a cash-flow intelligence dashboard for lender review, not a lender or decision-maker.","messages":[{"id":1,"message_key":"reminders.payment","params":{"name":"Mitali Kirana","amount":8986.34},"text":"নমস্কার Mitali Kirana। দয়া করে ₹8,986.34 টাকার পরের EMI দেখুন। এটি একটি সিমুলেটেড রিমাইন্ডার।","language":"bn"}]}
```
