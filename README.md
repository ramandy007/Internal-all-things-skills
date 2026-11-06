# InternalAllTheThings as Agent Skills

An [Agent Skills](https://agentskills.io) conversion of the
[InternalAllTheThings](https://github.com/swisskyrepo/InternalAllTheThings) corpus by Swissky:
**22 skills** covering Active Directory, internal network operations, cloud, red team tradecraft,
C2, containers, MSSQL, CI/CD and command reference — with **178 reference guides** behind
progressive disclosure.

Each skill is a small navigator (`SKILL.md`, 1–2.5k tokens) plus a `references/` directory holding
the full converted guides. An agent loads the navigator when the skill matches its task, and opens
only the reference file it actually needs.

## Coverage

| | |
|---|---|
| Upstream guides converted | 167 (100% of `docs/`, excluding the repo README and disclaimer) |
| Reference files produced | 178 (oversized guides split into parts) |
| Skills | 22 |
| Metadata cost of the full catalog | ~2.5k tokens (only `name` + `description` load at startup) |
| License | upstream terms — see [NOTICE.md](NOTICE.md) |

## Layout

```
.
├── skills/                      # the deliverable: 22 skill directories
│   ├── internal-engagement-playbook/
│   │   ├── SKILL.md             # navigator (frontmatter + instructions)
│   │   └── references/          # converted upstream guides, loaded on demand
│   ├── active-directory-kerberos/
│   └── ...
├── skills.json                  # machine-readable manifest of all skills
├── NOTICE.md                    # attribution and upstream terms
├── build/
│   ├── mapping.yaml             # taxonomy: upstream guide -> skill/reference mapping
│   ├── build.py                 # converts + splits + link-rewrites + emits skeletons
│   ├── validate.py              # spec + quality gate validator
│   ├── manifest.py              # regenerates skills.json and this catalog table
│   └── AUTHORING.md             # rules used to write the SKILL.md navigators
└── repo/                        # upstream clone (source of truth, unmodified)
```

## Install

A skill is just a directory containing `SKILL.md`. Copy the ones you want into the skills directory
your client scans:

```bash
# VS Code / GitHub Copilot (project scope)
mkdir -p .agents/skills && cp -r skills/* .agents/skills/

# Claude Code (personal scope)
mkdir -p ~/.claude/skills && cp -r skills/* ~/.claude/skills/

# Claude Code (project scope)
mkdir -p .claude/skills && cp -r skills/* .claude/skills/
```

For any other Agent Skills client, point it at this `skills/` directory or copy the directories into
the location it documents. Copying all 22 skills is cheap: only the `name` and `description` of each
load at startup.

Pick a subset if you prefer, e.g. only the AD stack:

```bash
cp -r skills/internal-engagement-playbook skills/active-directory-* /path/to/skills/
```

## Skill catalog

<!-- CATALOG:START -->
| Skill | Use it for | Refs |
|---|---|---|
| [`active-directory-certificates`](skills/active-directory-certificates/SKILL.md) | Exploit Active Directory Certificate Services (AD CS): ESC1 through ESC15 misconfigurations, certificate template and CA abuse,… | 18 |
| [`active-directory-credentials`](skills/active-directory-credentials/SKILL.md) | Steal and abuse Active Directory credentials: LSASS, SAM and NTDS.dit dumping, hash capture and cracking, pass-the-hash,… | 14 |
| [`active-directory-domain-escalation`](skills/active-directory-domain-escalation/SKILL.md) | Escalate from a foothold to domain or forest compromise: ZeroLogon, PrintNightmare, NoPAC/sAMAccountName spoofing, MS14-068,… | 11 |
| [`active-directory-enterprise-systems`](skills/active-directory-enterprise-systems/SKILL.md) | Compromise enterprise management and deployment infrastructure in Windows environments: SCCM/MECM (site takeover, network access… | 5 |
| [`active-directory-enumeration`](skills/active-directory-enumeration/SKILL.md) | Enumerate an Active Directory domain with PowerView, BloodHound, NetExec, impacket and native Windows tools: users, groups,… | 11 |
| [`active-directory-kerberos`](skills/active-directory-kerberos/SKILL.md) | Attack Kerberos in Active Directory: Kerberoasting, AS-REP roasting, Timeroasting, ticket forging (golden, silver, bronze bit),… | 9 |
| [`active-directory-lateral-movement`](skills/active-directory-lateral-movement/SKILL.md) | Move laterally and coerce authentication in Active Directory: NTLM relay (SMB, LDAP, HTTP, AD CS), Kerberos relay, authentication… | 4 |
| [`aws-security`](skills/aws-security/SKILL.md) | Assess and attack AWS: access-token and key abuse, IAM privilege escalation, IMDSv1/v2 metadata SSRF, S3 bucket exposure, EC2,… | 13 |
| [`azure-entra-security`](skills/azure-entra-security/SKILL.md) | Assess and attack Microsoft Azure and Entra ID (Azure AD): token and refresh-token abuse, enumeration with AzureHound/ROADtools,… | 22 |
| [`c2-frameworks`](skills/c2-frameworks/SKILL.md) | Operate command-and-control frameworks: Cobalt Strike (listeners, profiles, beacons, kits and artifacts), Metasploit Framework… | 5 |
| [`cicd-supply-chain-security`](skills/cicd-supply-chain-security/SKILL.md) | Assess CI/CD pipelines and the software supply chain: GitHub Actions, GitLab CI, Azure DevOps, CircleCI, Buildkite, Drone CI… | 9 |
| [`container-security`](skills/container-security/SKILL.md) | Assess Docker and Kubernetes: exposed Docker socket, privileged containers, host mounts and namespace escapes, Kubernetes API and… | 2 |
| [`ibm-cloud-security`](skills/ibm-cloud-security/SKILL.md) | IBM Cloud reference notes for managed databases (PostgreSQL, MongoDB) and object storage (COS): supported engines, storage… | 2 |
| [`internal-engagement-playbook`](skills/internal-engagement-playbook/SKILL.md) | Plan and run an authorized internal-network penetration test end to end: scoping, host and network discovery, Active Directory… | 4 |
| [`mssql-security`](skills/mssql-security/SKILL.md) | Attack and audit Microsoft SQL Server: enumeration, audit checks, credential harvesting (linked servers, logins, SQL agent jobs),… | 5 |
| [`redteam-defense-evasion`](skills/redteam-defense-evasion/SKILL.md) | Evade Windows and Linux defenses: AMSI bypass, PowerShell and ETW logging evasion, Windows Defender and AppLocker/WDAC bypass,… | 11 |
| [`redteam-initial-access`](skills/redteam-initial-access/SKILL.md) | Gain initial access during red team operations: phishing, ClickFix, HTML smuggling, malicious Office documents (Excel, Word,… | 10 |
| [`redteam-persistence`](skills/redteam-persistence/SKILL.md) | Establish persistence on Windows, Linux and RDP sessions: registry, scheduled tasks, services, WMI, startup folders, DLL search… | 5 |
| [`redteam-pivoting`](skills/redteam-pivoting/SKILL.md) | Pivot through internal networks: SOCKS proxies, port forwarding, SSH tunnels, Chisel, Ligolo-ng, Meterpreter routes and multi-hop… | 2 |
| [`redteam-privilege-escalation`](skills/redteam-privilege-escalation/SKILL.md) | Escalate privileges on compromised Windows and Linux hosts: enumeration checklists, service and scheduled-task abuse, unquoted… | 6 |
| [`security-cheatsheets`](skills/security-cheatsheets/SKILL.md) | Quick command references for internal and red team work: Mimikatz modules, PowerShell one-liners and download cradles, network… | 8 |
| [`shell-cheatsheets`](skills/shell-cheatsheets/SKILL.md) | Ready-to-use reverse shell and bind shell payloads across Bash, Python, Perl, PHP, Ruby, Netcat, PowerShell, Java, Node, Go and… | 2 |
<!-- CATALOG:END -->

## How to use it

1. **Start with `internal-engagement-playbook`** for a new engagement. It carries the phase model
   and routes to the specialist skill for the current phase.
2. **Let the description pick the skill.** Descriptions are written to trigger on the task, not on
   the tool name — "I have domain credentials and need service-account hashes" activates
   `active-directory-kerberos`.
3. **Read the navigator, then one reference.** The "Reference map" table in each `SKILL.md` says
   which file to open for which situation. Do not read a whole `references/` directory.
4. **Two AMSI payload references are ~16k tokens each** (`amsi-bypass-payload-1.md`,
   `amsi-bypass-payload-2.md`). Grep them for the method name instead of reading end to end.

## Rebuild and validate

The pipeline is reproducible from the upstream clone:

```bash
python3 build/build.py            # regenerate references + missing SKILL.md skeletons
python3 build/validate.py         # spec + quality gates for all skills
python3 build/manifest.py         # refresh skills.json and the catalog table above
npx skills-ref validate skills/<name>   # official agentskills.io reference validator
```

`build/validate.py` enforces the specification (name rules, description length, frontmatter keys)
plus local quality gates: body under 500 lines / 5000 tokens, every link resolves, every reference
file is linked from its `SKILL.md`.

## Authorized use

Offensive security material. Use it only on systems you own or have explicit written permission to
test, within the agreed scope and the applicable law. See [NOTICE.md](NOTICE.md).
