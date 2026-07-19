# Stripe Diagnostic Playbook

Use only the sections relevant to the incident. Stripe Dashboard and CLI behavior changes; prefer the installed CLI's `--help` and current official documentation over memorized syntax.

## Evidence surfaces

| Surface | Use it to establish |
| --- | --- |
| Workbench Health | Account-wide alerts, event-generation failures, and time-bounded integration health signals |
| Workbench Logs | Exact API request/response, request ID, status, error code/parameter, API version, source, and target account |
| Workbench Events | Event existence, payload, resource, destination attempts, delivery status, and resend history |
| Webhooks/event destinations | URL, account/Connect scope, selected event types, API version, secret identity, enabled state, and attempts |
| Application ingress logs | Arrival time, signature outcome, route status, latency, event ID, and correlation ID |
| Handler/queue logs | Handler selection, idempotency decision, durable handoff, retries, and exception chain |
| Database/downstream systems | Committed state and externally visible side effects |

Do not use sensitive payload content as a correlation key when a Stripe ID is available.

## Read-only CLI patterns

Add an explicit CLI profile and the correct targeting flags to every command. Stripe CLI defaults to test mode; use `--live` only after confirming live mode. Use `--stripe-account acct_...` for a connected account or `--stripe-context ...` when the integration requires a context.

```bash
# Verify the account reached by the selected credentials and flags.
stripe get /v1/account

# Retrieve known evidence.
stripe events retrieve evt_...
stripe webhook_endpoints retrieve we_...
stripe get /v1/payment_intents/pi_...
stripe get /v1/invoices/in_...

# Narrow lists; add created bounds and event type where supported.
stripe events list --delivery-success=false --limit=20
stripe webhook_endpoints list --limit=100

# Observe new request logs during a controlled reproduction.
stripe logs tail
```

Do not place secret keys directly in saved shell history or incident reports. Prefer an already authenticated, clearly named CLI profile or the environment's approved secret-injection mechanism. Do not read unrelated credential stores.

## Webhook response patterns

| Observation | Investigate first |
| --- | --- |
| No event in Stripe | Wrong mode/account, operation did not create that event, asynchronous delay, unsupported destination/event type, or Health alert |
| Event exists, no attempt | Destination scope, event selection, destination enabled/created time, account versus Connect routing |
| DNS/TLS/connect failure | DNS, certificate chain/expiry, firewall, proxy, origin reachability, regional outage |
| `301`/`302`/`307`/`308` | Incorrect registered URL, canonical-host redirect, HTTP-to-HTTPS redirect, locale/auth middleware |
| `400` | Signature/raw-body failure, JSON parsing, schema/version assumption, handler validation |
| `401`/`403` | Auth/WAF/CSRF/bot protection incorrectly guarding the public webhook route |
| `404`/`405` | Wrong route, deployment mismatch, base path, HTTP method, framework routing |
| `408`/timeout | Slow synchronous work, cold start, dependency wait, response emitted too late |
| `409` | Application concurrency or deduplication implementation; inspect whether work committed |
| `429` | Edge/application rate limiting applied to Stripe or exhausted capacity |
| `5xx` | Unhandled exception, dependency failure, transaction/queue failure, resource exhaustion |
| `2xx`, effect missing | Wrong handler, swallowed error, ack before durable work, bad dedupe key, queue failure, rollback, stale metadata |
| Duplicated effect | Missing/late idempotency claim, non-atomic dedupe, replay plus automatic retry, non-idempotent downstream call |

Keep webhook responses fast. Verify, durably claim or enqueue, return success, and process heavy work asynchronously when the application's consistency model permits it.

## Signature checklist

1. Match the signing secret to the exact destination, mode, and account context. CLI forwarding uses the secret printed by that listener, not a Dashboard destination's secret.
2. Capture the request body as raw bytes before JSON parsing or middleware transformation.
3. Pass the raw body, exact `Stripe-Signature` header, and correct secret to an official Stripe library.
4. Check proxy decompression, character decoding, newline normalization, body parsers, and serverless/framework adapters.
5. Check server clock skew only after body, header, and secret identity.
6. Never log the full signature header, secret, or unredacted payload merely to debug verification.

## Event correctness checklist

- Deduplicate durably on event ID before side effects; make the claim atomic.
- Do not require event ordering. Retrieve related objects when a predecessor is absent.
- Record event ID, type, creation time, account/context, livemode, API version, handler version, and outcome.
- Decide whether business logic needs event-time snapshot data or current object state; document the choice.
- Handle deleted-object variants and nullable fields.
- Recognize that manual resend and Stripe automatic retry can overlap.
- Reconcile partial success: an event can be acknowledged while a downstream effect fails, or time out after the effect commits.

## Payment and subscription state

Use object-specific status and timestamps rather than a generic “paid” flag.

- Checkout: inspect Session mode/status/payment status, then its PaymentIntent or Subscription.
- One-time payment: inspect PaymentIntent status, latest Charge, balance transaction, refunds, disputes, and asynchronous payment method state.
- Invoice: inspect invoice status, amount paid/remaining, PaymentIntent or payments, charge, subscription, and attempt history.
- Subscription: inspect status, items and Prices, current period, cancellation fields, schedule, latest invoice, trial, and pending updates.
- Customer mismatch: compare customer ID, metadata, email only as supporting evidence, and target account/mode.
- Local mismatch: identify which webhook or synchronous API response should have produced the missing transition and whether it committed.

## Safe reproduction ladder

Prefer the lowest-risk step that can disprove a hypothesis:

1. Inspect historical logs, events, attempts, and current objects.
2. Run local unit/fixture tests using a redacted captured shape.
3. Forward sandbox events locally with `stripe listen --events <types> --forward-to <local-url>`.
4. Generate sandbox test objects/events with `stripe trigger <event>` only when synthetic fixtures are adequate.
5. Resend an existing sandbox event after idempotency review and approval.
6. Reproduce in live mode only with explicit authorization, a bounded plan, monitoring, and reconciliation.

## Mutating commands

The following is an example, not authorization to execute it:

```bash
stripe events resend evt_... --webhook-endpoint=we_...
```

Confirm syntax with `stripe events resend --help`. Record account, mode, connected-account/context flags, event, endpoint, expected effects, approval, and verification before execution.

## Current official references

- Workbench overview: https://docs.stripe.com/workbench/overview
- Stripe CLI usage: https://docs.stripe.com/stripe-cli/use-cli
- Webhook setup, security, retries, and ordering: https://docs.stripe.com/webhooks
- Webhook signature troubleshooting: https://docs.stripe.com/webhooks/signature
- Request IDs: https://docs.stripe.com/api/request_ids
- API errors: https://docs.stripe.com/api/errors
- Event types: https://docs.stripe.com/api/events/types
- API versioning: https://docs.stripe.com/api/versioning
