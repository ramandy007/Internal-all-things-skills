---
name: internal-engagement-playbook
description: >-
  Plan and run an authorized internal-network penetration test end to end: scoping, host and
  network discovery, Active Directory and cloud attack-surface mapping, phase-by-phase checklists,
  evidence collection, and vulnerability report writing. Use when starting an internal engagement,
  deciding the next phase of an attack path, planning recon coverage, writing a pentest report or
  finding, or when source-code review or mobile-app testing is part of the engagement. Routes to
  the specialized skills in this library (Active Directory, cloud, red team, C2, containers,
  MSSQL, CI/CD).
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "4"
  generated-by: build/build.py
---

# Internal Engagement Playbook

Entry point for an authorized internal-network engagement. This skill carries the phase model,
the evidence discipline and the routing table; the specialist skills in this library carry the
technique depth. Read it when you need to decide *which phase you are in and what to do next* —
not when you need a specific command (go straight to the specialist skill for that).

## When to use this skill

- Starting an engagement: scope confirmation, asset inventory, phase plan, tool baseline.
- Between phases: you have a foothold and must choose the next move (escalate, enumerate AD, move laterally, prove impact).
- External footprint and recon planning, when internet-facing assets are in scope.
- Writing or reviewing the report: structure, evidence, screenshots, severity, obfuscation.
- The engagement also includes source-code review or an Android app and you need a defensible method.
- Not for a single technique — use the routing table to jump to the specialist skill.

## First moves

1. **Write the scope down before any packet leaves your host.** In-scope CIDRs, domains, accounts,
   excluded hosts, test window, escalation contact. Every later step is bounded by that list.
2. **Inventory the external footprint** (only if in scope):
   ```bash
   subfinder -d example.com -silent | httpx -title -tech-detect -status-code -follow-redirects -jarm -asn -json -silent -ports 80,443
   ```
   The `httpx` output gives tech stack, CDN/WAF and status per host — the input to every later decision.
3. **Discover live hosts and services on the internal range**, saving output from the first scan:
   ```bash
   nmap -sn -n 192.168.1.0/24                            # live hosts, no DNS
   sudo nmap -sSV -p- 192.168.0.1 -oA internal_scan -T4   # full TCP + versions
   ```
4. **Identify the domain controller early.** A host answering 88/389/445/3268 is the pivot point
   for the whole AD half of the engagement; get its address before enumerating anything else.
5. **Open the specialist skill for your current phase** (routing table below) and work its
   "First moves" before improvising.
6. **Log as you go**: one line per action (timestamp, target, command, result) in an evidence file.
   The report is assembled from that file, not from memory.

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [bug-hunting-methodology.md](references/bug-hunting-methodology.md) | planning passive/active recon: external footprint, subdomains, tech fingerprint, hidden parameters, historical URLs, Next.js routes | shodan/favicon pivots, subfinder/amass/massdns, ffuf/gobuster/bfac, gau/waybackurls/CommonCrawl, x8/Arjun, httpx/cdncheck, katana, nuclei |
| [vulnerability-reports.md](references/vulnerability-reports.md) | writing the report or one finding, or reviewing evidence quality | report structure, finding structure (summary/impact/reproduction/recommendation/references/severity), obfuscation rules, common screenshot mistakes, Ghostwriter/pwndoc |
| [source-code-analysis.md](references/source-code-analysis.md) | the engagement includes source review and you need the tool chain | Semgrep (rules registries, CI runs), SonarQube, Psalm, CodeQL, Snyk, AI-assisted review plugins |
| [android-applications.md](references/android-applications.md) | the engagement includes an Android app | APK extraction, jadx/apktool static analysis, patch+resign, Frida/objection dynamic analysis, SSL pinning and root-detection bypass, adb/AVD |

## Workflow

Phases are ordered but not linear: any new credential or host reopens an earlier phase.

| # | Phase | Exit criterion | Go to |
|---|---|---|---|
| 0 | Scope and plan | scope list + asset inventory written | this skill |
| 1 | External recon (if in scope) | external asset list with tech/WAF per host | `bug-hunting-methodology.md` |
| 2 | Internal discovery | live hosts, open services, reachable subnets | `security-cheatsheets` (network-discovery), `redteam-pivoting` |
| 3 | Foothold | first code execution or valid credential on a host | `redteam-initial-access` |
| 4 | Host escalation | local admin / SYSTEM / root | `redteam-privilege-escalation` |
| 5 | AD enumeration | domain object and permission map (BloodHound) | `active-directory-enumeration` |
| 6 | Credential access | hashes, tickets or plaintext for a next hop | `active-directory-credentials` |
| 7 | Kerberos / AD CS | ticket or certificate usable as another identity | `active-directory-kerberos`, `active-directory-certificates` |
| 8 | Lateral movement | execution on a new host, or a relay/coercion chain | `active-directory-lateral-movement` |
| 9 | Domain escalation | Domain Admin or equivalent on the target domain | `active-directory-domain-escalation` |
| 10 | Enterprise systems | control of a system that deploys privileged software | `active-directory-enterprise-systems` |
| 11 | Cloud | cloud identity with meaningful permissions | `aws-security`, `azure-entra-security`, `ibm-cloud-security` |
| 12 | Containers / DB / CI | cluster, database or pipeline control | `container-security`, `mssql-security`, `cicd-supply-chain-security` |
| 13 | Objectives | agreed proof captured (data, access, persistence) | `redteam-persistence`, `c2-frameworks`, `redteam-defense-evasion` |
| 14 | Reporting | every finding has reproducible evidence | `vulnerability-reports.md` |

Rules that keep the engagement honest:

- **Do not skip phase 5.** Almost every internal path after the foothold is an AD path; enumerating
  before escalating avoids re-doing work.
- Record the *evidence* of each phase exit (command, output, timestamp), not just the conclusion.
- When a phase stalls, change the axis rather than repeating the same attempt: different protocol,
  different credential source, different host.

## Gotchas

- **Noise**: active recon and scanners are loud. Collect passively first (`gau`, Wayback, CommonCrawl,
  passive subfinder), then touch the target; agree the noise budget in the scope.
- **Wordlists**: technology-specific lists (Assetnote `httparchive_*`) beat generic ones; generic
  lists produce false confidence and misses.
- **Evidence discipline**: obfuscate secrets and PII, caption every figure, keep screenshots readable
  and light-mode, and include the command line in the screenshot. A cropped or blurred image can
  still leak the original inside the document archive.
- **Report structure is graded**: summary → impact → reproduction steps → recommendation →
  references → severity (CVSS). A finding without reproduction steps is not a finding.
- **Android work needs a lab**: emulator/device, proxy CA installed, and a rebuild+resign loop
  before dynamic analysis; expect pinning and root detection.
- **Scope creep**: an interesting out-of-scope host is still out of scope. Note it, do not touch it.

## Authorized use

For authorized engagements only: written permission, agreed scope, and the laws of the
jurisdiction. This library is offensive tooling; unauthorized use is a crime.

## Source

Converted from the upstream InternalAllTheThings methodology guides —
https://github.com/swisskyrepo/InternalAllTheThings — see NOTICE.md.
