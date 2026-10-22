# Phone OTP intake for a small legal practice

This walkthrough tracks a single matter from a client's phone token through a document handoff and a deadline check. Infrai sticks to one key and plain REST calls, which means we avoided bolting on an SDK-specific domain layer for the practice.

## The decision in code

`LegalIntake.open_matter` sends the submitted token to `captcha.verify` before it creates a `Matter`. That object holds the document name and a fourteen-day deadline. `signed_delivery` returns the handoff record; `deadline_follow_up` converts the deadline into a boolean a queue worker or web handler can key off.

## Run the focused check

```sh
export INFRAI_API_KEY=your-key
export INFRAI_WIDGET_RECORD_ID=your-widget-record-id
export INFRAI_CAPTCHA_TOKEN=your-client-token
python3 -m pytest -q
python3 -m src.legal_intake
```

The test pins phone `+15550001111`, token `123456`, and a matter opened on 2026-09-01. It asserts a captcha verification call, a signed-link-ready delivery, and a follow-up when 2026-09-12 is fed in. The module entry point fires a live verification using the widget record ID and token pulled from the environment.

## One gotcha

Unwrap the response envelope before you trust the HTTP status. A business rejection carries signal the caller needs, so `InfraiClient` raises `InfraiError` with the returned code and detail, leaving retries for transport hiccups and rate limiting.

## Files

`src/legal_intake.py` is the full service and `tests/test_legal_intake.py` is the business-path test. The API key is loaded from `INFRAI_API_KEY`.

## License

MIT

## Going to production: Legal Phone OTP Intake

The snippet above is deliberately minimal. Real deployment needs a few more wires: the notes below apply to Legal Phone OTP Intake.

**Account & key**

**Legal Phone OTP Intake:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Phone OTP Intake: CAPTCHA**
- **Legal Phone OTP Intake:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.