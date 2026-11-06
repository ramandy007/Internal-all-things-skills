# Authoring guide — SKILL.md files

Read this before writing any `SKILL.md`. It defines the structure, the quality bar, and the
hard limits the validator enforces.

## Mission

Each skill is a **navigator** over a set of reference files converted from the
InternalAllTheThings corpus. The reference files already contain the deep technical detail
(commands, tool flags, payloads). Your job is to write the thin, high-signal layer that lets an
agent:

1. decide in ~5 seconds whether this skill applies,
2. know which reference file to open for its specific situation,
3. avoid the non-obvious mistakes that cost time.

You are **not** writing a tutorial and **not** summarising every reference. Duplicating reference
content wastes the agent's context — the whole point of progressive disclosure is that the agent
loads a reference only when it needs it.

## Target audience

An autonomous security agent (or a competent operator) mid-engagement. It already knows what
Kerberos, NTLM, SMB, LSASS, AD CS, S3, or a SOCKS proxy are. It does **not** know: which guide in
this corpus covers its exact sub-problem, which tool flags are current, which prerequisite must be
true before a technique works, or which of five near-identical techniques to pick.

Write for that gap.

## Mandatory structure

Use exactly these sections, in this order (level-2 headings). Keep the frontmatter that already
exists in the file — do not change `name`, and only touch `description` if it is factually wrong.

```markdown
# <Title>

One short paragraph (2-4 sentences): what this skill covers, the mental model of the domain,
and what "done" looks like.

## When to use this skill

- Bulleted, concrete situations / preconditions ("you hold any valid domain user credentials")
- Include the decision boundary: when this skill is the right one, and what to use instead
  (name the sibling skill, e.g. "for ticket forgery after escalation, see `active-directory-kerberos`")

## First moves

Numbered list of 3-7 **concrete commands** an operator runs first, copied or derived from the
references, each with one line on what to look for in the output. This is the highest-value
section — it must be executable as-is.

```bash
# example: what you run, with the actual flags
```

## Reference map

A table with one row per reference file in `references/`. **Every file must appear** (the
validator fails otherwise). Columns: file link, "read it when", key content.

| Reference | Read it when | Key content |
|---|---|---|
| [kerberoasting.md](references/kerberoasting.md) | you need service-account hashes and have any domain user | SPN discovery, GetUserSPNs, Rubeus modes, cracking |

Order the rows by the order an operator would need them, not alphabetically.

## Workflow

The decision sequence across references: phases, branch points, and "if you see X, open Y"
routing. Short numbered steps or a compact flow. This is where cross-reference judgment lives.

## Gotchas

Non-obvious, hard-won details: prerequisites that silently fail, version/tooling caveats,
detection or OPSEC side effects, destructive actions to avoid, output formats that differ
between tools. Bullets, no filler.

## Authorized use

One or two sentences: these techniques are for authorized engagements only, with explicit
permission and within the agreed scope.

## Source

One line: converted from the upstream InternalAllTheThings guides (link to
https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
```

## Hard limits (validator enforces)

| Check | Limit |
|---|---|
| `name` | must equal the directory name, `[a-z0-9-]`, no leading/trailing `-`, no `--` |
| `description` | 1-1024 chars, must contain an explicit trigger clause ("Use when …") |
| frontmatter keys | only `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` |
| body length | ≤ 500 lines **and** ≤ 5000 estimated tokens; target 1200-2500 tokens |
| links | every relative link must resolve on disk |
| reference coverage | every `references/*.md` must be linked from `SKILL.md` |
| body | must not be the `<!-- BODY TODO -->` placeholder |

Run it yourself before reporting:

```bash
python3 build/validate.py <your-skill-name> [<more-skill-names>...]
```

Aim for `OK` with zero warnings. Warnings about body size mean the skill is too verbose — cut.

## Quality bar

**Do:**
- Use the actual tool names, flags and syntax that appear in the references (`certipy find -u … -dc-ip …`, `netexec ldap … --kerberoast`, `GetUserSPNs.py -request`).
- State preconditions: required rights, signing state, patch level, OS/tool version.
- Distinguish near-identical techniques by the observable difference that selects between them.
- Note what breaks: "fails when SMB signing is enforced", "only works pre-2019 patch level", "triggers Defender signature X".
- Cross-link sibling skills by name instead of duplicating their content.

**Do not:**
- Write generic advice ("enumerate thoroughly", "use strong passwords", "consider OPSEC").
- Invent commands, flags or tool output that is not supported by the references.
- Paste large payloads or long code blocks — link the reference instead.
- Repeat the same paragraph in several skills.
- Add a table of contents, badges, or decorative structure.
- Mention that you are an AI, or address the reader as a student.

**Calibration example.** Weak:

> Kerberoasting is a technique that allows attackers to request service tickets and crack them offline. It is a common attack path in Active Directory.

Strong:

> Any authenticated domain user can request an RC4 service ticket for an account with an SPN, then crack it offline. Prefer accounts with `PasswordLastSet` older than the password policy and `msDS-SupportedEncryptionTypes` without AES — those yield RC4 tickets that crack in minutes instead of hours. `Rubeus.exe kerberoast /stats` first to size the target set.

## Process

1. Read `build/index/<skill>.md` — it lists every reference with line count, token estimate and
   its H2 sections. This is your map.
2. Read the smallest/highest-signal references in full; skim the large ones (grep for the
   technique name). Never read a >15k-token reference end to end.
3. Draft `SKILL.md` following the mandatory structure.
4. Run the validator; fix every error; cut until warnings are gone.
5. Re-read your own "First moves": would an operator copy-paste them correctly? Fix flags if not.

## Coordination rules

- Write **only** `SKILL.md` inside your assigned skill directories. Never edit `references/`,
  `build/`, `NOTICE.md`, `README.md`, or another teammate's skill.
- Do not run `build/build.py` (it rewrites references; the Lead owns it).
- Report back: skills completed, validator status, anything you could not verify.
