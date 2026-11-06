#!/usr/bin/env python3
"""Validate the generated skill library against the agentskills.io spec + local quality gates.

Checks per skill:
  * SKILL.md exists and has YAML frontmatter with required `name` and `description`
  * name: 1-64 chars, [a-z0-9-] only, no leading/trailing hyphen, no '--', equals directory name
  * description: 1-1024 chars, non-empty
  * only spec-allowed frontmatter keys
  * body: not a placeholder, <= 500 lines, <= 5000 estimated tokens (warn > 4000)
  * every relative link in SKILL.md resolves on disk
  * every references/*.md file is linked from SKILL.md (progressive disclosure is discoverable)
  * no reference file is unreachable / no dangling link

Usage:
  python3 build/validate.py                     # all skills
  python3 build/validate.py <skill> [<skill>..] # subset
  python3 build/validate.py --json out.json
Exit code 0 = no errors (warnings allowed).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
PLACEHOLDER = "<!-- BODY TODO -->"
MAX_DESC = 1024
MAX_BODY_LINES = 500
MAX_BODY_TOKENS = 5000


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    raw = text[4:end]
    try:
        fm = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return {"__error__": str(exc)}, text[end + 5:]
    return (fm if isinstance(fm, dict) else {"__error__": "frontmatter is not a mapping"}), text[end + 5:]


def validate_skill(skill_dir: Path) -> dict:
    name = skill_dir.name
    res = {"skill": name, "errors": [], "warnings": [], "metrics": {}}
    md = skill_dir / "SKILL.md"

    if not md.is_file():
        res["errors"].append("SKILL.md missing")
        return res

    text = md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None:
        res["errors"].append("missing or malformed YAML frontmatter")
        fm = {}
    if "__error__" in fm:
        res["errors"].append(f"frontmatter YAML error: {fm['__error__']}")
        fm = {}

    # --- name
    fm_name = fm.get("name")
    if not fm_name:
        res["errors"].append("frontmatter: missing required `name`")
    else:
        if not isinstance(fm_name, str):
            res["errors"].append("frontmatter: `name` must be a string")
        else:
            if not NAME_RE.match(fm_name):
                res["errors"].append(f"name {fm_name!r} violates [a-z0-9-] / hyphen rules")
            if len(fm_name) > 64:
                res["errors"].append(f"name too long ({len(fm_name)} > 64)")
            if fm_name != name:
                res["errors"].append(f"name {fm_name!r} != directory {name!r}")

    # --- description
    desc = fm.get("description")
    if not desc or not str(desc).strip():
        res["errors"].append("frontmatter: missing/empty `description`")
    else:
        d = " ".join(str(desc).split())
        res["metrics"]["description_chars"] = len(d)
        if len(d) > MAX_DESC:
            res["errors"].append(f"description too long ({len(d)} > {MAX_DESC})")
        if len(d) < 120:
            res["warnings"].append(f"description very short ({len(d)} chars) - weak trigger surface")
        if not re.search(r"\buse (when|for|after|before|during|to|if)\b", d.lower()):
            res["warnings"].append("description lacks an explicit 'Use when ...' trigger clause")

    # --- unexpected keys
    for key in fm:
        if key not in ALLOWED_KEYS:
            res["errors"].append(f"frontmatter: unsupported key {key!r}")

    # --- body
    if PLACEHOLDER in body:
        res["errors"].append("SKILL.md body is still the build placeholder")
    stripped = body.strip()
    if len(stripped) < 300:
        res["errors"].append(f"SKILL.md body too thin ({len(stripped)} chars)")
    lines = body.count("\n") + 1
    tokens = est_tokens(body)
    res["metrics"].update(body_lines=lines, body_tokens_est=tokens)
    if lines > MAX_BODY_LINES:
        res["errors"].append(f"body too long: {lines} lines > {MAX_BODY_LINES}")
    if tokens > MAX_BODY_TOKENS:
        res["errors"].append(f"body too heavy: ~{tokens} tokens > {MAX_BODY_TOKENS}")
    elif tokens > 4000:
        res["warnings"].append(f"body heavy: ~{tokens} tokens (target < 2500)")

    # --- links + reference coverage
    refs_dir = skill_dir / "references"
    ref_files = sorted(p.name for p in refs_dir.glob("*.md")) if refs_dir.is_dir() else []
    res["metrics"]["reference_files"] = len(ref_files)

    linked = set()
    for target in LINK_RE.findall(body):
        if re.match(r"^(https?:|mailto:|tel:|#)", target):
            continue
        path_part = target.split("#")[0]
        if not path_part:
            continue
        resolved = (skill_dir / path_part).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            res["errors"].append(f"link escapes the library root: {target}")
            continue
        if not resolved.exists():
            res["errors"].append(f"broken link: {target}")
        if path_part.startswith("references/"):
            linked.add(Path(path_part).name)

    missing = [r for r in ref_files if r not in linked]
    if missing:
        res["errors"].append(f"{len(missing)} reference file(s) not linked from SKILL.md: {', '.join(missing[:6])}")

    # --- cross-skill mentions must name a real skill (catch typos like active-directory-kerbros)
    known = {d.name for d in SKILLS.iterdir() if d.is_dir()}
    for token in set(re.findall(r"`([a-z][a-z0-9-]{6,60})`", body)):
        if token in known or token.endswith(".md"):
            continue
        near = [k for k in known if abs(len(k) - len(token)) <= 3 and levenshtein(k, token) <= 2]
        if near:
            res["warnings"].append(f"possible skill-name typo: `{token}` (did you mean {', '.join(near)}?)")

    # --- references must be non-trivial markdown
    for ref in ref_files:
        p = refs_dir / ref
        content = p.read_text(encoding="utf-8")
        if not content.strip():
            res["errors"].append(f"empty reference: {ref}")
        if not content.startswith("<!-- provenance:"):
            res["warnings"].append(f"reference lacks provenance comment: {ref}")

    return res


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_out = None
    if "--json" in sys.argv:
        json_out = sys.argv[sys.argv.index("--json") + 1]

    if args:
        dirs = [SKILLS / a for a in args]
        for d in dirs:
            if not d.is_dir():
                print(f"no such skill directory: {d}")
                return 2
    else:
        dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())

    results = [validate_skill(d) for d in dirs]
    errors = sum(len(r["errors"]) for r in results)
    warnings = sum(len(r["warnings"]) for r in results)

    print(f"{'skill':40s} {'refs':>4s} {'lines':>5s} {'~tok':>5s}  status")
    print("-" * 78)
    for r in results:
        m = r["metrics"]
        status = "OK" if not r["errors"] else f"{len(r['errors'])} ERROR(S)"
        if not r["errors"] and r["warnings"]:
            status = f"ok ({len(r['warnings'])} warn)"
        print(
            f"{r['skill']:40s} {m.get('reference_files', 0):4d} {m.get('body_lines', 0):5d} "
            f"{m.get('body_tokens_est', 0):5d}  {status}"
        )
    print("-" * 78)
    print(f"{len(results)} skills | {errors} errors | {warnings} warnings")

    for r in results:
        if r["errors"] or r["warnings"]:
            print(f"\n[{r['skill']}]")
            for e in r["errors"]:
                print(f"  ERROR   {e}")
            for w in r["warnings"]:
                print(f"  warning {w}")

    if json_out:
        Path(json_out).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"\nJSON report: {json_out}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
