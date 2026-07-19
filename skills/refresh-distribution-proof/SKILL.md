---
name: refresh-distribution-proof
description: Rebuild and verify cross-platform distribution evidence from one immutable source revision. Use when refreshing release packages, package reports, APK device proof, screenshots, audio checks, persistence traces, or promotion evidence while preventing secret leakage and stale or mixed-build artifacts.
---

# Refresh Distribution Proof

Produce a coherent evidence set whose packages and device captures all trace to the same source. Treat missing physical hardware, mismatched hashes, stale captures, and leaked credentials as hard failures.

## Workflow

1. Freeze the source identity.
   - Require a clean checkout unless the task explicitly defines a reproducible dirty-tree hash.
   - Record the commit and source-tree hash before building.
   - Abort if either identity changes before all formats and evidence are complete.

2. Rebuild every related format.
   - Build all requested platform/runtime/format rows in one run or isolated staging directory.
   - Do not reuse packages or proof from an earlier revision.
   - Preserve each package report beside its artifact, including source hash, artifact hash, target, runtime, format, architecture, and toolchain identity.

3. Enforce provenance before testing.
   - Compare the source hash in every package report; require one identical value matching the frozen source.
   - Recompute artifact hashes and require exact matches with their reports.
   - Stop before device work if any report is absent, ambiguous, or inconsistent.

4. Handle credentials disposably.
   - Create temporary signing credentials only in a restrictive temporary directory.
   - Pass credentials through opaque references or environment/file descriptors supported by the tool; never place secret bytes in source, argv, logs, reports, screenshots, or archives.
   - Delete temporary credentials in a guaranteed cleanup path after packaging.
   - Scan the final evidence and package trees for credential filenames, private-key markers, passwords, and known secret values. Fail if any match remains.

5. Install the exact APK under evidence.
   - Select the APK by its package report, not by a glob such as “latest.”
   - Recompute its hash immediately before installation and compare it with the report.
   - Install that exact path, then record the artifact hash, application ID, version/build, device serial, and install command result in the device trace.
   - Reject a capture if a different APK was installed or the installed identity cannot be tied back to the report.

6. Refresh runtime evidence.
   - Remove or quarantine old screenshots, recordings, audio checks, and persistence traces so stale files cannot satisfy the gate.
   - Capture fresh launch and interaction screenshots from the newly installed build.
   - Exercise audible events and record the project-approved audio evidence, distinguishing an audio-path check from visual proof.
   - Mutate durable state, terminate the app, relaunch it, and capture a trace proving the state survived.
   - Hash every evidence file and write those hashes into the proof manifest.

7. Fail closed on device requirements.
   - When the requirement says physical device, verify and record hardware identity plus emulator/simulator detection results.
   - Never substitute an emulator, simulator, desktop window, or host-only smoke test for physical-device evidence.
   - Mark the row failed or blocked when compliant hardware is unavailable; do not promote it based on partial proof.

8. Finalize atomically.
   - Recheck source identity, package report hashes, installed APK hash, evidence hashes, credential scan, and required-device classification.
   - Publish or replace the evidence set only after every required check passes.
   - Report each target row as passed, failed, or blocked with its exact reason; never collapse missing proof into success.

## Evidence Minimum

Require the final manifest to connect this chain:

`source identity -> package report -> artifact hash -> installed artifact -> device identity -> fresh evidence hashes`

Keep commands project-specific. Discover and use the repository's owning package, proof, and validation commands rather than inventing parallel scripts or manifests.
