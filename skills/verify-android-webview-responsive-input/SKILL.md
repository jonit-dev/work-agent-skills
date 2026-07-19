---
name: verify-android-webview-responsive-input
description: Verify an Android APK's WebView UI and pointer input across landscape viewport sizes, including iframe or nested-frame apps. Use when Codex must prove responsive Android visuals, diagnose parent-WebView versus iframe viewport mismatches through Chrome DevTools Protocol, correct cross-frame pointer-coordinate scaling, exercise interactive controls, or demonstrate that evidence came from the exact APK under test.
---

# Verify Android WebView Responsive Input

Verify the installed APK, rendered pixels, coordinate spaces, and resulting app state as one evidence chain. Do not substitute a desktop browser preview for APK proof.

## Establish the exact build

1. Record the local APK absolute path, SHA-256, byte size, package ID, version name, and version code.
2. Record `adb devices -l`, Android version, model, display size, density, and current rotation settings.
3. Install that APK explicitly with `adb install -r <apk>` and launch its package/activity.
4. Confirm the running package and version with `dumpsys package`.
5. Resolve the installed base APK with `pm path <package>`, pull it, and compare its SHA-256 with the local file. Treat a mismatch as a failed exact-APK check until explained.

Keep the artifact hash beside every screenshot and interaction report. Reinstall and restart the app after rebuilding; never assume the device contains the latest output.

## Capture native and forced-size visuals

Test at least:

- The device's native landscape size.
- A smaller forced landscape size that stresses layout compression.
- A second materially different aspect ratio when the supported device range warrants it.

For each case:

1. Force landscape and wait for configuration changes and rendering to settle.
2. Apply `adb shell wm size <width>x<height>` when testing a forced size.
3. Query `wm size`, capture a PNG with `screencap`, and inspect the PNG dimensions. Do not infer the effective viewport from the requested size.
4. Check clipping, letterboxing, safe-area overlap, unreadable scaling, hidden controls, and distorted canvas or frame content.
5. Save a screenshot plus the effective display and viewport measurements.

Record the original size, density, and rotation settings before mutation. Restore them with `wm size reset`, `wm density reset` when changed, and the original rotation settings even if verification fails.

## Inspect viewport ownership with CDP

Enable WebView debugging in a debuggable build, locate the running WebView DevTools socket, and forward it through ADB. Inspect the targets exposed by `http://127.0.0.1:<port>/json`.

Measure each relevant browsing context separately:

- Top-level `window.innerWidth`, `innerHeight`, `devicePixelRatio`, and `visualViewport`.
- The iframe element's bounding rectangle or box quad in its parent.
- Child-frame `innerWidth`, `innerHeight`, and target element rectangles.
- Screenshot pixel dimensions and Android's effective display dimensions.

Use the CDP frame tree and execution contexts to evaluate expressions in the correct frame. A responsive failure can exist even when the child frame looks correct in isolation: the parent may size, crop, or scale it incorrectly. Preserve a compact table of parent viewport, frame rectangle, child viewport, DPR, screenshot size, and forced display size for every test case.

## Map cross-frame pointer coordinates

Treat these as distinct coordinate spaces:

1. Target element coordinates inside the child frame.
2. Child viewport coordinates.
3. Frame rectangle coordinates in the parent viewport.
4. Top-level CSS viewport coordinates used by CDP input.
5. Physical display coordinates used by `adb shell input tap`.

For an untransformed iframe, map a child point approximately as:

```text
parentX = frameLeft + childX * frameWidth / childInnerWidth
parentY = frameTop  + childY * frameHeight / childInnerHeight
```

Account for frame borders, scrolling, CSS transforms, visual-viewport offsets, and nested frames. Prefer box quads over simple rectangles when transforms exist, and apply the mapping once per frame boundary.

Map top-level CSS coordinates to physical screenshot/display coordinates only after measuring both spaces:

```text
physicalX = cssX * screenshotWidth  / topLevelViewportWidth
physicalY = cssY * screenshotHeight / topLevelViewportHeight
```

Do not multiply blindly by `devicePixelRatio`; Android display scaling, CDP CSS pixels, WebView zoom, and iframe scaling can already account for part of the conversion. Confirm mappings with hit tests such as `elementFromPoint` in the correct context before dispatching input.

Use top-level CSS coordinates for CDP pointer events. Use physical display coordinates for ADB taps. Never send child-local coordinates directly to either surface.

## Verify interactive behavior

Exercise representative controls at every viewport size:

- A control near each important edge or corner.
- A primary action and a secondary action.
- Canvas, board, drag, or gesture input when present.
- At least one control inside each relevant frame boundary.

For every action, prove an observable outcome: changed app state, control value, selected item, navigation, game move, emitted event, or a before/after screenshot. A delivered `pointerdown`, `pointerup`, or `click` is insufficient if the application state does not change as expected.

When input misses:

1. Compare the element center in child coordinates with the recursively mapped parent point.
2. Run hit testing at both the expected and actual points.
3. Check parent/child viewport ratios, frame scroll, CSS transforms, WebView zoom, visual viewport offsets, and system bars.
4. Retry through CDP and ADB separately to isolate CSS-space mapping from physical-space mapping.
5. Fix the owning layout or input mapping, then rerun all sizes.

## Report evidence and verdict

Produce a per-size result containing:

- Exact local and installed APK hashes and version metadata.
- Device identity, Android/WebView versions, orientation, effective display size, and screenshot dimensions.
- Parent, frame, and child viewport measurements.
- Input method, source coordinates, mapped coordinates, hit-test target, and observed state change.
- Screenshot and trace paths.
- A clear pass, fail, or blocked verdict with the first actionable mismatch.

Pass only when the exact APK is verified, native and forced landscape visuals are acceptable, representative controls cause the expected state changes, and coordinate mappings are measured rather than assumed. Mark device-only or signing gaps explicitly; do not convert absence of evidence into a platform-support claim.
