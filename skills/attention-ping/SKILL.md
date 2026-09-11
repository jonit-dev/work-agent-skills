---
name: attention-ping
description: Ping the user by ntfy when an agent is blocked and needs them.
---

# Attention Ping

notify the user on their phone when Codex or Claude Code cannot safely continue without their immediate attention.

Use the bundled `scripts/ping_attention.py`; it reads `~/.config/ntfy/joi-alarms.env`. Never read the topic or token into chat, command output, source code, commits, or task text.

## Trigger contract

Send **one** ping only when all of these are true:

1. Work is actively blocked or a time-sensitive decision is waiting.
2. The user must personally provide input, approve an external/irreversible action, resolve access, or make a consequential choice.
3. There is no safe useful work left to do while waiting.
4. The final chat/terminal response clearly states the same blocker and exact action needed.

Good triggers: approval required to deploy or send; missing credential must be entered by the user; a destructive choice needs confirmation; ambiguous requirements would materially change the result; an autonomous run is stalled and cannot continue.

Do **not** ping for routine completion, progress, test failures you can investigate, ordinary questions, low-value status, a background job finishing, or anything you can resolve safely yourself. A ping is an interrupt, not a substitute for reasoning.

## Send

From this skill directory:

```bash
python3 scripts/ping_attention.py \
  --title "Codex needs your decision" \
  --message "Project: <name>. Blocker: <one sentence>. Action: <exact response needed>."
```

Use `Claude needs your attention` for Claude Code. Keep the message short, actionable, and free of secrets, tokens, private customer data, stack traces, or large logs. Include the project/repository name when useful.

The script sends ntfy priority `max` with an alarm tag. It suppresses an identical title/message for 15 minutes across agents to prevent retry-loop spam. Exit code `0` means either ntfy accepted the message or a duplicate was deliberately suppressed; JSON output distinguishes `sent` from `suppressed`. Any other exit code means delivery failed—report that failure in the terminal response and do not claim the user was notified.

## Quiet hours (23:00-09:00)

The user is asleep between 23:00 and 09:00 local time and must never be woken. The script enforces this
itself: a ping issued inside that window is published to ntfy with a `Delay` header targeting 09:00
that morning, and reports `"status": "scheduled"` with `deliver_at`. Exit code is `0` — that is a
success. Do not retry it, do not fall back to `curl`, do not use another notifier to get through.

Say "ping scheduled for 09:00" rather than "notified" when reporting a quiet-hours ping.

## Verification

Before relying on it in a workflow, run a no-network check:

```bash
python3 scripts/ping_attention.py --dry-run \
  --title "Codex needs your decision" \
  --message "Project: smoke test. Blocker: verification only. Action: none."
```

A real HTTP acceptance proves publication only. Phone sound/vibration depends on Android ntfy notification settings; do not claim the phone made sound from server acceptance alone.
