# Timezone Scheduling Validation Matrix

Use explicit ISO instants, IANA zones, and a frozen clock. Compute expected values independently of the helper under test.

## Minimum unit matrix

| Case | Required assertion |
| --- | --- |
| UTC ordinary time | Local-to-instant and instant-to-local identity |
| Negative-offset zone | Local calendar date can differ from UTC date |
| Positive-offset zone | Next local day can begin on prior UTC date |
| Half-hour zone | Offset is not rounded to whole hours |
| Spring-forward gap | Documented reject/shift policy is applied |
| Fall-back overlap | Documented earlier/later policy selects exact instant |
| Before/after DST change | Recurrence retains intended local time if contracted |
| Cross-midnight event | Both local dates/views include or place it correctly |
| Month/year rollover | Bounds and drag destination use correct year/month |
| Leap day | Date arithmetic and persistence preserve February 29 |

Include zones such as `UTC`, `America/Vancouver`, `Europe/Berlin`, `Asia/Kolkata`, and a non-DST positive-offset zone. Use the product's supported-zone set when narrower.

## Boundary-query pattern

For a requested local calendar range:

1. Construct local start and exclusive local end in the authoritative timezone.
2. Convert both bounds to instants.
3. Query `timestamp >= startInstant AND timestamp < endInstant`.
4. Assert an event exactly at the exclusive end appears only in the next range.
5. Repeat for DST-short and DST-long local days; never assume 24 elapsed hours.

## Drag/drop journeys

Exercise these separately:

- same day, ordinary hour;
- across local midnight while UTC date remains unchanged;
- across UTC midnight while local date remains unchanged;
- into a spring-forward gap;
- onto each occurrence of a fall-back overlap;
- last day of month to first day of next month;
- December to January;
- month view to day/week view, then refresh.

For each journey assert request payload, stored instant, response value, local rendered label, visual slot, duration, and post-refresh position.

## Manual browser checklist

- Set browser/system timezone different from the project/calendar timezone.
- Open day, week, and month views around both DST transitions.
- Confirm headings, grid slots, event dates, and labels use the configured timezone.
- Create or schedule an event, refresh, navigate views, and confirm it does not shift.
- Drag across midnight and a month boundary; inspect the network payload and reload.
- Verify ambiguous/nonexistent-time UX matches the documented policy.

Record browser, OS timezone, configured timezone, frozen/test date, screenshots or video, network payload, stored value, and result. Helper-unit output is not a substitute for this evidence.

## Common false confidence

- Using `new Date('YYYY-MM-DD')` and assuming local-date semantics.
- Adding `24 * 60 * 60 * 1000` to advance one local day.
- Formatting without passing a timezone.
- Testing only UTC.
- Mocking the calendar component and claiming drag/drop correctness.
- Asserting displayed text without verifying persisted instant and refresh.
- Using the same implementation to calculate both actual and expected values.
