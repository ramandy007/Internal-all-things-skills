#!/usr/bin/env python3
"""Grounding QA for SKILL.md navigators.

Checks that a navigator is structural and *grounded* in its own references:
  1. every mandated section is present
  2. "First moves" actually contains executable code
  3. the Reference map lists as many rows as there are reference files
  4. every tool/command token used in a code block appears somewhere in that skill's references
     (catches invented commands and flags)

Usage: python3 build/qa.py [skill ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

SECTIONS = [
    "When to use this skill",
    "First moves",
    "Reference map",
    "Workflow",
    "Gotchas",
    "Authorized use",
    "Source",
]
CODE_RE = re.compile(r"```[a-zA-Z0-9]*\n(.*?)```", re.DOTALL)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|\s*\[[^\]]+\]\(references/[^)]+\)", re.MULTILINE)
# a leading command token: optional prompt, optional path, then the binary
CMD_RE = re.compile(r"^(?:\$|PS>|#)?\s*(?:\./|\.\\|/[\w./-]+/)?([A-Za-z][\w.+-]{1,40})")


def sections(body: str) -> dict[str, str]:
    parts = H2_RE.split(body)
    out = {}
    for i in range(1, len(parts), 2):
        out[parts[i].strip().lower()] = parts[i + 1]
    return out


def commands_in(body: str) -> list[str]:
    found = []
    for block in CODE_RE.findall(body):
        for line in block.splitlines():
            s = line.strip()
            if not s or s.startswith(("#", "//", ">", "<", "-", "*", "|")):
                continue
            m = CMD_RE.match(s)
            if m:
                found.append(m.group(1))
    return found


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dirs = [SKILLS / a for a in args] if args else sorted(d for d in SKILLS.iterdir() if d.is_dir())
    problems = 0
    for d in dirs:
        md = d / "SKILL.md"
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        body = text.split("\n---\n", 1)[1] if text.startswith("---\n") and "\n---\n" in text else text
        refs_dir = d / "references"
        refs = sorted(p.name for p in refs_dir.glob("*.md"))
        corpus = "\n".join((refs_dir / r).read_text(encoding="utf-8", errors="replace") for r in refs).lower()

        issues = []
        secs = sections(body)
        for name in SECTIONS:
            if name.lower() not in secs:
                issues.append(f"missing section: ## {name}")

        fm = secs.get("first moves", "")
        if not CODE_RE.search(fm):
            issues.append("'First moves' has no code block")

        rows = len(TABLE_ROW_RE.findall(body))
        if rows != len(refs):
            issues.append(f"Reference map lists {rows} reference rows, directory has {len(refs)}")

        ungrounded = []
        for cmd in sorted(set(commands_in(body))):
            low = cmd.lower()
            if low in corpus:
                continue
            # allow generic shell builtins / prompts
            if low in {"cat", "echo", "cd", "ls", "export", "set", "if", "for", "then", "fi"}:
                continue
            ungrounded.append(cmd)
        if ungrounded:
            issues.append("tools not found in this skill's references: " + ", ".join(ungrounded))

        if issues:
            problems += 1
            print(f"[{d.name}]")
            for i in issues:
                print(f"  - {i}")
        else:
            print(f"[{d.name}] grounded OK ({len(refs)} refs)")

    print(f"\n{problems} skill(s) with findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
