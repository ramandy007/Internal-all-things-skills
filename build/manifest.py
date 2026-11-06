#!/usr/bin/env python3
"""Regenerate skills.json and the catalog table in README.md from the skill directories."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
START, END = "<!-- CATALOG:START -->", "<!-- CATALOG:END -->"
TRIGGER_RE = re.compile(r"\bUse (when|for|after|before|during|to|if)\b", re.IGNORECASE)


def frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    return yaml.safe_load(text[4:end]) or {}


def first_h1(text: str) -> str:
    fence = False
    for line in text.splitlines():
        if line.strip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if not fence and line.startswith("# "):
            return line[2:].strip()
    return ""


def one_line_purpose(desc: str, limit: int = 130) -> str:
    desc = " ".join(desc.split())
    m = TRIGGER_RE.search(desc)
    head = desc[: m.start()].strip() if m else desc
    head = head.rstrip(" .,;:")
    if len(head) <= limit:
        return head
    cut = head[:limit].rsplit(" ", 1)[0]
    return cut + "…"


def main() -> int:
    entries = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        md = d / "SKILL.md"
        if not md.is_file():
            print(f"skip {d.name}: no SKILL.md", file=sys.stderr)
            continue
        text = md.read_text(encoding="utf-8")
        fm = frontmatter(text)
        refs = sorted((d / "references").glob("*.md"))
        body = text.split("\n---\n", 1)[1] if "\n---\n" in text else text
        entries.append(
            {
                "name": fm.get("name", d.name),
                "title": first_h1(text) or fm.get("name", d.name),
                "description": " ".join(str(fm.get("description", "")).split()),
                "path": f"skills/{d.name}",
                "references": len(refs),
                "reference_tokens_est": sum(max(1, p.stat().st_size // 4) for p in refs),
                "body_tokens_est": max(1, len(body) // 4),
                "purpose": one_line_purpose(str(fm.get("description", ""))),
            }
        )

    total_refs = sum(e["references"] for e in entries)
    manifest = {
        "schema": "agentskills-library-manifest/1",
        "upstream": "https://github.com/swisskyrepo/InternalAllTheThings",
        "upstream_commit": "203bb0c0b290bf7c9158c32d43523b8d66f292c1",
        "spec": "https://agentskills.io/specification",
        "license": "upstream terms - see NOTICE.md",
        "counts": {"skills": len(entries), "references": total_refs},
        "skills": entries,
    }
    (ROOT / "skills.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    rows = [
        "| Skill | Use it for | Refs |",
        "|---|---|---|",
    ]
    for e in entries:
        rows.append(f"| [`{e['name']}`]({e['path']}/SKILL.md) | {e['purpose']} | {e['references']} |")
    table = "\n".join(rows)

    readme = README.read_text(encoding="utf-8")
    if START in readme and END in readme:
        pre = readme.split(START)[0]
        post = readme.split(END)[1]
        README.write_text(f"{pre}{START}\n{table}\n{END}{post}", encoding="utf-8")
        print("README catalog updated")
    else:
        print("README markers not found - catalog not written", file=sys.stderr)

    print(f"skills.json: {len(entries)} skills, {total_refs} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
