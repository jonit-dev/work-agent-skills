---
name: stripe-debugging
description: Diagnose Stripe integration incidents safely across arbitrary Stripe accounts, sandboxes, live mode, Connect platforms, and connected accounts. Use for webhook delivery or signature errors, missing/duplicate/out-of-order events, API request failures, Workbench logs and Health alerts, payment or subscription state mismatches, Stripe CLI investigations, endpoint availability, retries, and reconciliation. Bind every investigation to the account and mode specified or discovered at runtime; never assume a particular account, project, credential source, framework, or deployment.
---

# Stripe Debugging

Diagnose from evidence and keep the investigation account-agnostic. Treat Stripe object state as external production state and application logs, persistence, and side effects as separate evidence surfaces.

## Establish the target

Create an investigation header before querying Stripe:

```text
Account: <display name and acct_... when available>
Mode: <sandbox/test/live>
Context: <account/platform/connected account/organization>
CLI profile or credential source: <non-secret identifier>
Connected account or Stripe context: <acct_.../context/none>
Incident window: <start..end, timezone>
Known IDs: <req_..., evt_..., we_..., pi_..., in_..., sub_..., cs_..., cus_...>
Symptom: <observable failure>
```

- Resolve values from the user, repository, deployment configuration, Dashboard account selector, or authenticated CLI profile.
- Ask one concise question if account, mode, or Connect context remains ambiguous. Never silently choose.
- Verify the authenticated account with a read-only request before relying on results. For the CLI, prefer `stripe get /v1/account` plus the explicit profile, `--live`, `--stripe-account`, or `--stripe-context` flags that apply.
- Repeat the account, mode, and Connect context before any consequential command.
- Never print, paste, commit, or summarize secret keys or webhook signing secrets. Redact authorization headers, client secrets, payment details, personal data, and full payload fields that are not needed.

## Work read-only first

Do not mutate Stripe or application state merely because the user asked to debug. Start with:

1. Capture the exact error, first failure time, last known success, affected flow, and stable identifiers.
2. Build one UTC timeline from application logs, Stripe request logs, Events, webhook delivery attempts, persistence writes, queues, and downstream side effects.
3. Inspect Stripe Workbench in this order: Health, Logs, Events, then Webhooks/event destinations.
4. Correlate by IDs rather than timestamps alone. Preserve `Request-Id`, event ID, endpoint ID, object IDs, HTTP status, API version, account context, attempt time, and response body.
5. Retrieve the current authoritative Stripe objects involved. Do not infer payment or subscription state from one event or from local database state alone.
6. Trace application handling from ingress through signature verification, parsing, routing, idempotency claim, persistence, queueing, and side effects.
7. Form competing hypotheses and run the smallest read-only check that distinguishes them.

Read [references/diagnostic-playbook.md](references/diagnostic-playbook.md) for failure patterns, object-state checks, and current command examples. Run `stripe <resource> <operation> --help` before using a CLI command because installed CLI versions differ.

## Diagnose webhook incidents

Separate these layers explicitly:

```text
event generation -> destination selection -> network/TLS/gateway -> route
-> raw-body signature verification -> parsing/version -> handler
-> idempotency/persistence -> queue/downstream side effect
```

- Confirm that the event exists in the correct account and mode before investigating delivery.
- Confirm destination scope: account, Connect, or organization; subscribed event types; enabled state; endpoint URL; event payload style; and destination API version.
- Inspect every delivery attempt and the exact endpoint response. Redirects are not successful webhook handling.
- For signature failures, compare the destination's signing secret to the deployed secret without exposing either. Ensure verification uses the unmodified raw request body, the received `Stripe-Signature` header, and the secret for that exact destination and mode.
- For `2xx` with missing business effects, inspect swallowed exceptions, acknowledgment before durable handoff, wrong handler routing, stale metadata, idempotency collisions, transaction rollbacks, queue failures, and downstream timeouts.
- Expect duplicate delivery and non-guaranteed ordering. Require durable event-ID deduplication and handlers that retrieve missing objects or tolerate predecessor events arriving later.
- Distinguish snapshot from thin events and retrieve the current object where the event contract requires it.

## Diagnose API and state incidents

- Use Stripe request logs and `Request-Id` to locate the exact request, response, API version, account context, error type, code, parameter, and idempotency key.
- Treat `resource_missing` first as a possible mode/account/connected-account mismatch, then as an ID or lifecycle issue.
- Compare the API version used by the request, SDK, account, and event destination. Never “fix” an old event by retrieving it under a newer version; event payloads are immutable.
- Reconstruct the relevant object graph. Examples: Checkout Session to PaymentIntent or Subscription; Invoice to PaymentIntent, Charge, Customer, and Subscription; Subscription to items, Price, schedule, and latest invoice.
- Separate Stripe truth, local persistence, and user-visible state. Identify the first divergent transition.
- Check Health alerts when symptoms span unrelated endpoints, event generation, or a time-bounded platform issue.

## Control mutations

Require explicit user authorization before resending an event, replaying a job, changing an event destination, rotating a secret, creating test data, or altering/refunding/capturing/canceling any Stripe object. Treat live-mode actions as especially consequential.

Before a resend or replay:

1. Confirm the exact event, endpoint, account, mode, and Connect context.
2. Prove the handler and every downstream side effect are idempotent for this event.
3. Explain that a manual resend does not cancel Stripe's automatic retry schedule.
4. Predict expected state changes and define rollback or reconciliation steps.
5. Capture before-state, perform only the approved action, then verify Stripe state, local state, and side effects.

Never use a generated test event as proof that a historical production payload will succeed. Reproduce payload shape, API version, account context, and handler configuration when testing.

## Report the result

Lead with the finding and confidence. Include:

- Bound account, mode, Connect context, incident window, and affected identifiers
- Timeline and evidence, with secrets and unnecessary personal data redacted
- Root cause or ranked hypotheses, clearly separating fact from inference
- Blast radius and whether automatic retries remain pending
- Smallest remediation and any reconciliation required
- Validation performed across Stripe, the application, and downstream state
- Residual risks, monitoring, and any action still requiring approval

If evidence is insufficient, say exactly which account-scoped artifact would discriminate the remaining hypotheses.
