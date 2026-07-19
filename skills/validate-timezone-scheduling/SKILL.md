---
name: validate-timezone-scheduling
description: Validate timezone-aware scheduling and calendar behavior across DST transitions, local day/week/month boundaries, drag-and-drop, parsing, formatting, and UTC persistence. Use when reviewing or testing schedulers, editorial calendars, appointments, cron timing, recurring events, date filters, or UI flows that translate local wall-clock intent into stored instants.
---

# Validate Timezone Scheduling

Start by distinguishing an absolute instant from local wall-clock intent. Never let a bare date, offset, browser timezone, or server timezone silently decide semantics.

## Define the contract

1. Name the authoritative IANA timezone and its owner: user, project, campaign, event, or system.
2. Classify every value as an instant, zoned date-time, local date-time, local date, or recurrence rule.
3. Persist instants with an offset-aware type such as `TIMESTAMPTZ` or canonical ISO UTC. Persist timezone and recurrence intent separately when future occurrences must retain the same local time.
4. Specify policies for nonexistent spring-forward times and ambiguous fall-back times. Choose deliberately: reject, shift forward, or choose the earlier/later occurrence.
5. Trace parsing, calculation, serialization, API transport, database storage, and display. Flag every implicit `Date`, locale, or process-timezone conversion.

Read [validation-matrix.md](references/validation-matrix.md) when building tests or reviewing calendar interactions.

## Prove conversion invariants

- Parse wall-clock input only with its explicit IANA timezone and DST disambiguation policy.
- Format stored instants in the authoritative timezone, not whichever timezone executes the code.
- Assert `local intent + timezone -> instant -> same local representation` for valid times.
- Assert `instant -> local -> instant` preserves the exact instant when offset/disambiguation information is retained.
- Test positive, negative, half-hour, and non-DST zones; do not generalize from UTC and one North American zone.
- Freeze the clock and timezone in tests. Avoid assertions based on the current date, host locale, or developer machine.

## Validate calendar boundaries

- Calculate day, week, and month membership in the user's timezone before converting query bounds to instants.
- Test events near UTC midnight that belong to the previous or next local date.
- Test cross-midnight events, DST-short and DST-long days, week starts, month ends, leap days, and December/January rollover.
- Query with half-open intervals `[start, end)` to prevent duplicates at adjacent boundaries.
- Keep date-only values date-only. Parsing `YYYY-MM-DD` through an implicit UTC `Date` commonly shifts the displayed day.

## Validate drag and drop

- State whether moving an item preserves its local wall-clock time, duration, absolute instant, or recurrence pattern.
- Derive the destination in the calendar's authoritative timezone, then serialize the resulting instant.
- Test drops across DST, midnight, week, month, and year boundaries and between views.
- Assert the persisted instant, returned API value, rendered local slot, and refresh result all agree.
- Define behavior when the destination wall time is nonexistent or ambiguous.

## Separate evidence layers

- Unit-test pure conversion and boundary helpers with a table-driven matrix.
- Integration-test API/database round trips and stored types with the real serialization path.
- Browser-test rendered labels, placement, view navigation, drag/drop, refresh, and browser-timezone independence.
- Manually verify representative DST and boundary journeys in a real browser when production readiness depends on calendar behavior.
- Never claim browser proof from helper tests. Passing date utilities cannot prove the calendar library, DOM placement, interaction, API wiring, or refresh behavior.

## Report

Lead with contract ambiguity or user-visible date/time errors. For each finding give the input intent, timezone, expected instant/local display, observed behavior, affected boundary, and strongest available evidence. Distinguish verified browser behavior from helper-only or integration-only evidence.
