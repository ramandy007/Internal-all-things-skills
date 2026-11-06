# NOTICE

## Upstream source

This skill library is a derivative work built from **InternalAllTheThings** by Swissky (swisskyrepo)
and its contributors:

- Repository: <https://github.com/swisskyrepo/InternalAllTheThings>
- Snapshot commit: `203bb0c0b290bf7c9158c32d43523b8d66f292c1` (2026-08-16)
- Published site: <https://swisskyrepo.github.io/InternalAllTheThings/>

The markdown guides under each skill's `references/` directory are converted copies of the upstream
`docs/**/*.md` files. Conversion is mechanical: mkdocs-specific markup removed, relative links
rewritten to the new layout, oversized guides split into parts at section boundaries (with code
fences closed and reopened so every part stays valid), and a provenance comment added at the top of
each file. Technical content is unchanged.

Every reference file carries its origin:

```
<!-- provenance: InternalAllTheThings docs/<upstream-path> @ 203bb0c | part n/m: <title> | converted for Agent Skills; see ../../NOTICE.md -->
```

## Upstream terms

The upstream repository ships no separate LICENSE file. Its README and `DISCLAIMER.md` state that the
content is provided "as is, for learning purpose", that it is intended for educational and research
use, and that the authors take no responsibility for misuse. This library is redistributed on the
same basis: educational and research use, with attribution to the upstream authors, and no warranty
of any kind.

If you redistribute this library, keep this NOTICE and the provenance comments intact, and keep the
attribution to the upstream project and its contributors.

## What this library adds

- The 22-skill taxonomy and every `SKILL.md` navigator file.
- Reference splitting, link rewriting and provenance annotation (`build/build.py`).
- Validation and manifest tooling (`build/validate.py`, `build/manifest.py`) and the authoring guide
  (`build/AUTHORING.md`).

## Authorized use

The techniques documented here are offensive security techniques. Use them only on systems you own
or have explicit written permission to test, within the agreed scope and the applicable law.
Unauthorized use is a crime in most jurisdictions.
