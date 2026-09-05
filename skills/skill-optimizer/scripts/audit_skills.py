#!/usr/bin/env python3
"""Read-only audit for agent libraries using SKILL.md files."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
from pathlib import Path
import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "use",
    "using",
    "via",
    "when",
    "with",
}


def frontmatter_scalar(frontmatter: str, key: str) -> str:
    """Read a one-line YAML scalar without adding a YAML dependency."""
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*)$", frontmatter)
    return match.group(1).strip().strip("'\"") if match else ""


def routing_words(text: str) -> set[str]:
    """Return meaningful lowercase words for a rough overlap signal."""
    return {
        word
        for word in re.findall(r"[a-z0-9]+", text.lower())
        if len(word) > 2 and word not in STOP_WORDS
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit SKILL.md routing metadata and root-file size."
    )
    parser.add_argument("root", help="Root directory containing skills")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include archived or hidden skill directories",
    )
    parser.add_argument(
        "--description-warn",
        type=int,
        default=60,
        help="Flag descriptions longer than this many characters",
    )
    parser.add_argument(
        "--root-warn",
        type=int,
        default=20_000,
        help="Flag roots larger than this with no references directory",
    )
    return parser.parse_args()


def audit(args: argparse.Namespace) -> dict:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Skill root is not a directory: {root}")

    skills: list[dict] = []
    invalid: list[str] = []

    for path in sorted(root.rglob("SKILL.md")):
        relative_path = path.relative_to(root)
        if not args.include_hidden and any(
            part.startswith(".") for part in relative_path.parts
        ):
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.+)$", text, re.DOTALL)
        if not match:
            invalid.append(str(relative_path))
            continue

        frontmatter = match.group(1)
        name = frontmatter_scalar(frontmatter, "name")
        description = frontmatter_scalar(frontmatter, "description")
        references = list(path.parent.glob("references/*"))
        flags: list[str] = []

        if len(description) > args.description_warn:
            flags.append("long-description")
        if re.search(
            r"\b(any time|always|whenever|regardless of)\b",
            description,
            re.IGNORECASE,
        ):
            flags.append("aggressive-trigger")
        if len(text) > args.root_warn and not references:
            flags.append("large-root-no-references")
        if not name or not description:
            flags.append("missing-routing-metadata")

        skills.append(
            {
                "path": str(relative_path),
                "name": name,
                "description": description,
                "description_chars": len(description),
                "root_chars": len(text),
                "reference_files": len(references),
                "flags": flags,
            }
        )

    overlaps: list[dict] = []
    for index, left in enumerate(skills):
        left_words = routing_words(f"{left['name']} {left['description']}")
        for right in skills[index + 1 :]:
            right_words = routing_words(f"{right['name']} {right['description']}")
            union = left_words | right_words
            word_similarity = len(left_words & right_words) / len(union) if union else 0
            name_similarity = SequenceMatcher(
                None, left["name"], right["name"]
            ).ratio()
            if word_similarity >= 0.42 or name_similarity >= 0.72:
                overlaps.append(
                    {
                        "left": left["path"],
                        "right": right["path"],
                        "word_similarity": round(word_similarity, 2),
                        "name_similarity": round(name_similarity, 2),
                    }
                )

    return {
        "root": str(root),
        "skill_count": len(skills),
        "invalid_count": len(invalid),
        "invalid": invalid,
        "catalog_description_chars": sum(
            skill["description_chars"] for skill in skills
        ),
        "long_description_count": sum(
            "long-description" in skill["flags"] for skill in skills
        ),
        "aggressive_trigger_count": sum(
            "aggressive-trigger" in skill["flags"] for skill in skills
        ),
        "large_root_no_references_count": sum(
            "large-root-no-references" in skill["flags"] for skill in skills
        ),
        "flagged": sorted(
            (skill for skill in skills if skill["flags"]),
            key=lambda skill: (-skill["description_chars"], skill["path"]),
        ),
        "possible_overlaps": sorted(
            overlaps,
            key=lambda pair: (
                -max(pair["word_similarity"], pair["name_similarity"]),
                pair["left"],
                pair["right"],
            ),
        ),
    }


def print_text(result: dict) -> None:
    print(f"Skills: {result['skill_count']} | invalid: {result['invalid_count']}")
    print(f"Catalog description chars: {result['catalog_description_chars']}")
    print(
        "Long descriptions: "
        f"{result['long_description_count']} | aggressive triggers: "
        f"{result['aggressive_trigger_count']} | large roots without references: "
        f"{result['large_root_no_references_count']}"
    )

    print("\nFlagged skills:")
    for skill in result["flagged"]:
        flags = ", ".join(skill["flags"])
        print(
            f"- {skill['path']}: {flags} "
            f"({skill['description_chars']} description chars; "
            f"{skill['root_chars']} root chars)"
        )

    print("\nPossible overlaps (review; never auto-merge):")
    for pair in result["possible_overlaps"][:30]:
        print(
            f"- {pair['left']} <> {pair['right']} "
            f"(words={pair['word_similarity']}, names={pair['name_similarity']})"
        )


def main() -> int:
    args = parse_args()
    result = audit(args)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 1 if result["invalid_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
