---
name: discord-announcement
description: Generate a player-facing Discord announcement markdown file from unreleased changes. Diffs origin/master vs origin/release to find new features, balance changes, and bug fixes. Use when preparing patch notes, update announcements, or Discord community posts about what's new in the game.
---

# Discord Announcement Generator

Generate a `discord-announcement.md` with player-facing patch notes from unreleased commits.

## Steps

### 1. Fetch and Diff

```bash
git fetch origin
git log --oneline origin/release..origin/master
```

This shows all commits on master that haven't been deployed to release yet.

### 2. Gather Details

For each meaningful commit, read the actual code changes to understand the player impact:

```bash
git diff origin/release..origin/master --stat
git log origin/release..origin/master --format="%H %s"
```

For commits that look player-relevant, inspect the actual diff:

```bash
git show <hash> --stat
git diff <hash>~1 <hash> -- '*.ts' ':!*.test.*'
```

### 3. Classify Changes

Sort each commit into one of these player-facing categories (skip anything that doesn't fit):

- **New Features** — new gameplay mechanics, spells, items, maps, NPCs, quests
- **Balance Changes** — XP adjustments, damage/stat tweaks, drop rate changes, requirement changes
- **Bug Fixes** — things that were broken and now work correctly
- **Quality of Life** — UI improvements, notifications, spam reduction, convenience

**SKIP these (not player-facing):**
- `chore: bump build version`
- Test-only changes
- Internal refactors with no behavior change
- Code cleanup, logging changes
- Documentation changes
- CI/CD changes

### 4. Write the Announcement

Write `discord-announcement.md` in the project root.

**CRITICAL — Discord Free 2000 character limit:**
The output MUST be under **2000 characters total** (Discord free tier message limit). Count characters before finalizing. If it exceeds 2000, ruthlessly trim:
1. Merge related bullets into one
2. Drop less impactful items
3. Shorten descriptions — one clause, not a sentence
4. Remove tables — use inline text instead
5. If still over, split into multiple messages separated by `---` (each section under 2000 chars)

**Format:**

```markdown
# Update Notes

## New Features
- **Feature Name** — Brief description

## Balance Changes
- **What changed** — Old → New (with numbers)

## Bug Fixes
- Fixed [player-visible problem]

## Quality of Life
- Improvement description
```

**Writing rules:**
- Use player language, not developer language (e.g., "monsters" not "NPCs", "damage" not "EntityDamageCalculation")
- Be specific with numbers: "XP from variant monsters reduced from 1.5x to 1.2x" not "XP adjustments"
- Group related small fixes into one bullet when they're about the same system
- Omit empty categories
- Keep it ultra-concise — every word must earn its place
- Use bold for the key thing that changed in each bullet
- Do NOT mention internal class names, file paths, or technical implementation details
- Frame bug fixes positively: "Fixed X" not "X was broken because of Y internal reason"
- No tables (they eat character budget fast) — use inline format instead
- No emojis in headers (saves chars) unless the user requests them

### 5. Verify Character Count

Run `wc -c discord-announcement.md` and confirm it's under 2000. If over, trim further. If splitting into multiple messages, verify each section between `---` separators is under 2000.

### 6. Present to User

After writing the file, display its contents with the character count and ask if the user wants any adjustments before posting to Discord.
