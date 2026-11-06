#!/usr/bin/env python3
"""Build Agent Skills (agentskills.io spec) from the InternalAllTheThings docs corpus.

Reads build/mapping.yaml, then for every skill:
  * copies / splits the upstream guides into <skill>/references/
  * rewrites relative links (cross-reference aware) and split-file anchors
  * records provenance in an HTML comment
  * emits build/index/<skill>.json + .md (reference index for SKILL.md authors)
  * creates a starter SKILL.md with validated frontmatter (never overwrites a real body)

Usage:
  python3 build/build.py                 # build references + missing skeletons
  python3 build/build.py --frontmatter   # refresh frontmatter of existing SKILL.md files
  python3 build/build.py --check         # coverage report only
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "repo" / "docs"
SKILLS = ROOT / "skills"
BUILD = ROOT / "build"
COMMIT = "203bb0c"

FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


# --------------------------------------------------------------------------- util
def slugify(text: str) -> str:
    """GitHub/mkdocs-style anchor slug."""
    t = re.sub(r"`([^`]*)`", r"\1", text)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[*_~]", "", t)
    t = t.strip().lower()
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    t = re.sub(r"[\s]+", "-", t)
    return t.strip("-")


def iter_blocks(lines: list[str]):
    """Yield (index, line, in_fence) for every line."""
    fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fence = not fence
            yield i, line, True
            continue
        yield i, line, fence


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line_index, level, text) for headings outside fenced code blocks."""
    out = []
    for i, line, in_fence in iter_blocks(lines):
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def first_h1(lines: list[str]) -> str | None:
    for _, level, text in headings(lines):
        if level == 1:
            return text
    return None


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def collapse_blank(lines: list[str]) -> list[str]:
    """Collapse runs of 3+ blank lines outside fenced blocks to a single blank line."""
    out, blanks = [], 0
    for _, line, in_fence in iter_blocks(lines):
        if not in_fence and not line.strip():
            blanks += 1
            if blanks > 2:
                continue
        else:
            blanks = 0
        out.append(line)
    return out


# --------------------------------------------------------------------------- mapping
def load_mapping() -> dict:
    with open(BUILD / "mapping.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def expand_sources(mapping: dict) -> tuple[dict, list[dict]]:
    """Return (source_map, units).

    source_map: docs-relative source path -> {"skill", "ref"} (first ref for split sources)
    units: flat list of work items {"skill","src","ref","from","to","title","part","parts"}
    """
    source_map: dict[str, dict] = {}
    units: list[dict] = []
    for skill in mapping["skills"]:
        name = skill["name"]
        seen_refs = set()
        for src in skill["sources"]:
            src_path = src["src"]
            split = src.get("split")
            if split:
                parts = len(split)
                for idx, part in enumerate(split, 1):
                    unit = {
                        "skill": name,
                        "src": src_path,
                        "ref": part["ref"],
                        "from": part["from"],
                        "to": part["to"],
                        "title": part.get("title") or f"{src_path} (part {idx})",
                        "part": idx,
                        "parts": parts,
                        "split": True,
                    }
                    units.append(unit)
                source_map.setdefault(src_path, {"skill": name, "ref": split[0]["ref"]})
            else:
                unit = {
                    "skill": name,
                    "src": src_path,
                    "ref": src["ref"],
                    "from": None,
                    "to": None,
                    "title": None,
                    "part": 1,
                    "parts": 1,
                    "split": False,
                }
                units.append(unit)
                source_map[src_path] = {"skill": name, "ref": src["ref"]}
            if src["ref"] in seen_refs:
                raise SystemExit(f"duplicate ref {src['ref']} in skill {name}")
            seen_refs.add(src["ref"])
    return source_map, units


# --------------------------------------------------------------------------- transform
def rewrite_links(
    text: str,
    cur_skill: str,
    cur_ref: str,
    source_map: dict,
    src_dir: Path,
    split_anchor_map: dict[str, str] | None,
    assets: set[Path],
    warnings: list[str],
) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|tel:|#)", target):
            # anchor-only link inside a split part -> may live in a sibling part
            if target.startswith("#") and split_anchor_map:
                slug = target[1:]
                owner = split_anchor_map.get(slug)
                if owner and owner != cur_ref:
                    return f"]({owner}#{slug})"
            return m.group(0)

        # assets referenced with ./files/...
        if re.match(r"^\.?/?files/", target):
            rel = re.sub(r"^\./", "", target)
            assets.add((src_dir / rel).resolve())
            return f"]({rel})"

        path_part, _, anchor = target.partition("#")
        if not path_part or not re.match(r"^\.{1,2}/", path_part):
            return m.group(0)

        # resolve against the source file's directory
        resolved = (src_dir / path_part).resolve()
        try:
            rel = resolved.relative_to(DOCS.resolve()).as_posix()
        except ValueError:
            warnings.append(f"link escapes docs: {target}")
            return m.group(0)
        if not rel.endswith(".md"):
            rel = rel + ".md"

        dest = source_map.get(rel)
        if not dest:
            warnings.append(f"unresolved link target {target!r} in {cur_skill}/{cur_ref}")
            return m.group(0)
        if dest["skill"] == cur_skill:
            new = f"../{cur_skill}/references/{dest['ref']}"
            new = dest["ref"]  # same directory
        else:
            new = f"../../{dest['skill']}/references/{dest['ref']}"
        return f"]({new}" + (f"#{anchor}" if anchor else "") + ")"

    return LINK_RE.sub(repl, text)


def transform_unit(unit: dict, source_map: dict, all_units: list[dict], warnings: list[str]) -> tuple[str, set[Path]]:
    src_file = DOCS / unit["src"]
    raw = src_file.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    if unit["split"]:
        lo, hi = unit["from"] - 1, unit["to"]
        chunk = lines[lo:hi]

        # fence state entering/leaving this slice, so code blocks stay valid
        fence = False
        open_marker = ""
        for _, line, _ in iter_blocks(lines[:lo]):
            if FENCE_RE.match(line):
                fence = not fence
                if fence:
                    open_marker = line.strip()
        starts_in_fence = fence
        fence = False
        for _, line, _ in iter_blocks(lines[:hi]):
            if FENCE_RE.match(line):
                fence = not fence
        ends_in_fence = fence

        while chunk and not chunk[0].strip():
            chunk.pop(0)
        if unit["part"] > 1:
            chunk = [f"# {unit['title']}", ""] + chunk
        if starts_in_fence:
            chunk = chunk[:2] + [open_marker, ""] + chunk[2:]
        if ends_in_fence:
            chunk = chunk + ["```"]
    else:
        chunk = lines

    # anchor ownership map across sibling split parts
    split_anchor_map = None
    if unit["parts"] > 1:
        split_anchor_map = {}
        for u in all_units:
            if u["src"] != unit["src"]:
                continue
            if u["split"]:
                sib = lines[u["from"] - 1: u["to"]]
                if u["part"] > 1:
                    sib = [f"# {u['title']}", ""] + sib
            else:
                sib = lines
            for _, level, text in headings(sib):
                if level >= 2:
                    split_anchor_map.setdefault(slugify(text), u["ref"])

    body = "\n".join(collapse_blank(chunk)).rstrip() + "\n"
    assets: set[Path] = set()
    body = rewrite_links(
        body,
        unit["skill"],
        unit["ref"],
        source_map,
        src_file.parent,
        split_anchor_map,
        assets,
        warnings,
    )

    prov = f"<!-- provenance: InternalAllTheThings docs/{unit['src']} @ {COMMIT}"
    if unit["parts"] > 1:
        prov += f" | part {unit['part']}/{unit['parts']}: {unit['title']}"
    prov += " | converted for Agent Skills; see ../../NOTICE.md -->"
    body = prov + "\n\n" + body
    return body, assets


# --------------------------------------------------------------------------- emit
def emit_frontmatter(skill: dict, ref_count: int) -> str:
    desc = " ".join(skill["description"].split())
    return (
        "---\n"
        f"name: {skill['name']}\n"
        "description: >-\n"
        + "\n".join("  " + ln for ln in wrap(desc, 96))
        + "\n"
        "license: Upstream terms apply - see NOTICE.md\n"
        "metadata:\n"
        "  source: https://github.com/swisskyrepo/InternalAllTheThings\n"
        f"  source-commit: \"{COMMIT}\"\n"
        f"  reference-files: \"{ref_count}\"\n"
        "  generated-by: build/build.py\n"
        "---\n"
    )


def wrap(text: str, width: int) -> list[str]:
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def ref_index(skill: dict, units: list[dict]) -> dict:
    items = []
    for u in units:
        p = SKILLS / skill["name"] / "references" / u["ref"]
        text = p.read_text(encoding="utf-8")
        lines = text.splitlines()
        items.append(
            {
                "ref": f"references/{u['ref']}",
                "file": u["ref"],
                "title": first_h1(lines) or u["ref"],
                "source": f"docs/{u['src']}",
                "lines": len(lines),
                "tokens_est": est_tokens(text),
                "headings": [t for _, lvl, t in headings(lines) if lvl == 2][:60],
            }
        )
    return {
        "skill": skill["name"],
        "title": skill.get("title", skill["name"]),
        "description": " ".join(skill["description"].split()),
        "references": items,
        "total_tokens_est": sum(i["tokens_est"] for i in items),
    }


def write_index_md(idx: dict) -> str:
    out = [f"# {idx['title']} ({idx['skill']})", "", f"References: {len(idx['references'])} | tokens ~{idx['total_tokens_est']}", ""]
    out.append("| # | ref | title | lines | ~tokens | key sections |")
    out.append("|---|-----|-------|-------|---------|--------------|")
    for n, it in enumerate(idx["references"], 1):
        secs = "; ".join(it["headings"][:8]).replace("|", "/")
        out.append(f"| {n} | `{it['file']}` | {it['title']} | {it['lines']} | {it['tokens_est']} | {secs} |")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontmatter", action="store_true", help="refresh frontmatter of existing SKILL.md")
    ap.add_argument("--check", action="store_true", help="coverage report only, no writes")
    args = ap.parse_args()

    mapping = load_mapping()
    source_map, units = expand_sources(mapping)

    # ---- coverage check against the actual corpus
    excluded = set(mapping["upstream"]["excluded"])
    corpus = {
        p.relative_to(DOCS).as_posix()
        for p in DOCS.rglob("*.md")
        if p.relative_to(DOCS).as_posix() not in excluded
    }
    missing = sorted(corpus - set(source_map))
    extra = sorted(set(source_map) - corpus)
    dupes = [s for s in source_map if sum(1 for u in units if u["src"] == s and u["part"] == 1) > 1]
    print(f"corpus guides : {len(corpus)}")
    print(f"mapped sources: {len(source_map)}")
    print(f"skills        : {len(mapping['skills'])}")
    print(f"reference files: {len(units)}")
    if missing:
        print("MISSING:", *missing, sep="\n  ")
    if extra:
        print("EXTRA (not in repo):", *extra, sep="\n  ")
    if dupes:
        print("DUPLICATE:", *dupes, sep="\n  ")
    if missing or extra or dupes:
        print("coverage check FAILED")
        return 1
    print("coverage check OK")
    if args.check:
        return 0

    # ---- validate split boundaries land on H2 headings
    warnings: list[str] = []
    for u in units:
        if not u["split"]:
            continue
        src_lines = (DOCS / u["src"]).read_text(encoding="utf-8", errors="replace").splitlines()
        fence_at = {}
        fence = False
        for n, line in enumerate(src_lines, 1):
            if FENCE_RE.match(line):
                fence = not fence
            fence_at[n] = fence
        for boundary in (u["from"], u["to"] + 1):
            if boundary == 1 or boundary - 1 >= len(src_lines):
                continue
            ln = src_lines[boundary - 1]
            if fence_at.get(boundary, False):
                continue  # deliberate cut inside a code block (fence is closed/reopened)
            if not re.match(r"^##\s", ln):
                warnings.append(f"split boundary {boundary} of {u['src']} is not an H2: {ln[:60]!r}")

    # ---- write references
    for skill in mapping["skills"]:
        sdir = SKILLS / skill["name"]
        (sdir / "references").mkdir(parents=True, exist_ok=True)

    for u in units:
        body, assets = transform_unit(u, source_map, units, warnings)
        dest = SKILLS / u["skill"] / "references" / u["ref"]
        dest.write_text(body, encoding="utf-8")
        for src_asset in assets:
            if not src_asset.exists():
                warnings.append(f"missing asset {src_asset}")
                continue
            rel = src_asset.relative_to(DOCS.resolve()).as_posix()
            tgt = dest.parent / "files" / src_asset.name
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_asset, tgt)

    # ---- indexes + skeletons
    for skill in mapping["skills"]:
        s_units = [u for u in units if u["skill"] == skill["name"]]
        idx = ref_index(skill, s_units)
        (BUILD / "index").mkdir(exist_ok=True)
        (BUILD / "index" / f"{skill['name']}.json").write_text(json.dumps(idx, indent=2) + "\n", encoding="utf-8")
        (BUILD / "index" / f"{skill['name']}.md").write_text(write_index_md(idx), encoding="utf-8")

        skill_md = SKILLS / skill["name"] / "SKILL.md"
        fm = emit_frontmatter(skill, len(s_units))
        if not skill_md.exists():
            skill_md.write_text(fm + "\n<!-- BODY TODO -->\n", encoding="utf-8")
        elif args.frontmatter:
            old = skill_md.read_text(encoding="utf-8")
            if old.startswith("---"):
                _, _, rest = old.partition("\n---\n")
                skill_md.write_text(fm + rest, encoding="utf-8")
            else:
                skill_md.write_text(fm + old, encoding="utf-8")

    print(f"\nwrote {len(units)} reference files under {SKILLS}")
    if warnings:
        print(f"\n{len(warnings)} warnings:")
        for w in warnings:
            print("  -", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
