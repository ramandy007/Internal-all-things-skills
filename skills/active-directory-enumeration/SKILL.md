---
name: active-directory-enumeration
description: >-
  Enumerate an Active Directory domain with PowerView, BloodHound, NetExec, impacket and native
  Windows tools: users, groups, computers, trusts, GPOs, ACLs/ACEs, AD-integrated DNS, shares,
  RODC, machine account quota and the AD recycle bin. Use when starting an AD engagement, when
  mapping domain objects and permissions, when you hold any valid domain credentials or a null
  session and need to find attack paths, or when reviewing AD security posture. Includes AD
  operations from Linux (ldapsearch, impacket, netexec, bloodyAD).
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "11"
  generated-by: build/build.py
---

# Active Directory Enumeration and Recon

Enumeration in AD is permission mapping, not user listing: every object you can read carries an
ACL, and every ACL edge is a potential escalation. The deliverables are (1) a BloodHound graph or
equivalent inventory of objects and rights, (2) a short list of edges you can actually traverse
with the credentials you hold, and (3) the prerequisites each edge needs — a writable SPN, a
misconfigured GPO link, a machine account quota, an ADIDNS zone. Done means you can name the next
hop, the right that enables it, and what you must not touch to get there.

## When to use this skill

- You have any valid domain credential, an NTLM hash, a ccache ticket, or a null/guest session and
  need to know what the domain looks like and where the edges are.
- You need object/ACL data (users, groups, computers, trusts, GPOs, OUs) rather than a single
  technique execution.
- You are reviewing AD posture and need to report dangerous group membership, stale `adminCount`
  objects, unconstrained delegation, or writable GPO/OU paths.
- Operating from Linux against AD — ccache/keytab reuse, SSSD credential extraction, GSSAPI SSH.

Use `active-directory-credentials` instead when the goal is extracting secrets (NTDS, LAPS, GMSA,
DPAPI). Use `active-directory-kerberos` for roasting and ticket forgery after you have found the
target account. Use `active-directory-certificates` for AD CS escalation — only its enumeration
step belongs here. Use `active-directory-lateral-movement` once you are choosing a relay or
coercion path.

## First moves

1. **Map the domain graph.** BloodHound data first, from Linux or Windows:

   ```bash
   bloodhound-python -d domain.local -u username -p password -gc LAB2008DC01.domain.local -c all
   # Windows: all collection omits GPOLocalGroup unless requested explicitly
   # .\SharpHound.exe -c all,GPOLocalGroup --OutputDirectory C:\Windows\Temp --randomfilenames --throttle 10000
   ```

   Look for: shortest paths from owned principals to Domain Admins, unconstrained delegation
   computers, sessions on high-value hosts.

2. **Enumerate writable objects as your user.** This is the highest-yield single query; it turns
   enumeration straight into an attack list:

   ```bash
   bloodyAD --host 10.10.10.10 -d attack.lab -u john.doe -p 'Password123*' get writable \
     --otype USER --right WRITE --detail | egrep -i 'distinguishedName|servicePrincipalName'
   ```

   Rows with an empty `servicePrincipalName` are targeted-Kerberoasting candidates.

3. **Find privileged-by-attribute accounts.** `adminCount=1` marks protected accounts and never
   clears automatically:

   ```bash
   nxc ldap 10.10.10.10 -u username -p password --admin-count
   ```

4. **Check machine account quota and AD CS in the same pass.** MAQ > 0 enables
   attacker-created computers (RBCD, relay); certipy `find` surfaces template misconfigurations:

   ```bash
   nxc ldap <ip> -u user -p pass -M maq
   certipy find 'corp.local/john:Passw0rd@dc.corp.local' -vulnerable -hide-admins -bloodhound
   ```

5. **Hunt sessions without credentials** if you only have a guest/null session — RID cycling
   reconstructs the user list:

   ```bash
   netexec smb 10.10.11.231 -u guest -p '' --rid-brute 10000 --log rid-brute.txt
   ```

   Look for RIDs 500 (`Administrator`), 502 (`krbtgt`), and service-looking account names.

6. **Sweep shares for both read exposure and write-drop opportunities:**

   ```bash
   nxc smb 10.0.0.4 -u guest -p '' -M spider_plus
   smbmap -H 10.10.10.10 -r PATH
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [domain-enumeration.md](references/domain-enumeration.md) | always first — you need the object inventory | SharpHound/SOAPHound/BloodHound.py collectors, PowerView and AD-module command sets, user hunting, RID cycling, DC discovery |
| [ad-from-linux.md](references/ad-from-linux.md) | your foothold is Linux, or you need Kerberos material from a Linux host | ccache reuse from /tmp, keyring and SSSD KCM, keytab extraction, `sssd.conf` deobfuscation, GSSAPI SSH abuse via UPN rewrite |
| [groups.md](references/groups.md) | you are deciding which built-in group membership is actually worth pursuing | AdminSDHolder/SDProp, DNSAdmins DLL load, Backup Operators SeBackup/SeRestore, Schema Admins |
| [acl-ace.md](references/acl-ace.md) | `get writable` returned an ACE you need to convert into access | GenericAll/GenericWrite (SPN, preauth, scriptPath), WriteDACL→DCSync, WriteOwner, ReadLAPS/ReadGMSA, ForceChangePassword, OU ACL and OUned |
| [group-policy-objects.md](references/group-policy-objects.md) | you have write rights on a GPO or its link and want execution | GPO ACL discovery, SharpGPOAbuse, pyGPOAbuse, StandIn, GroupPolicyBackdoor, GPOHound |
| [shares.md](references/shares.md) | shares are readable or writable — content theft or hash farming | smbmap/smbclient/spider_plus/Snaffler enumeration; SCF, URL, library-ms and searchConnector drops with Responder |
| [adidns.md](references/adidns.md) | you need name resolution to point at you, or DNS records are readable | adidnsdump, dnstool, bloodyAD dnsRecord, wildcard + Inveigh, unauthenticated RFC 2136 updates |
| [machine-account-quota.md](references/machine-account-quota.md) | you plan to create a computer account | MAQ default of 10, `msDS-CreatorSID` counting, `addcomputer.py` |
| [rodc.md](references/rodc.md) | the domain has an RODC | RODC golden ticket, key list attack with `-rodcKey`/`-rodcNo`, abusing `msDS-RevealOnDemandGroup` |
| [recycle-bin.md](references/recycle-bin.md) | deleted objects may hold stale privileged ACLs or secrets | LIST_CHILD on Deleted Objects, restore rights, `bloodyAD set restore` |
| [tricks.md](references/tricks.md) | Kerberos auth fails with a time error | 5-minute clock skew, `smb2-time` probe, `faketime` |

## Workflow

1. **Establish a credential base.** Null/guest → RID cycling and share sweep; one valid user →
   BloodHound collection. Record the domain SID and DC list while you are there.
2. **Collect the graph.** `bloodhound-python -c all` (or SharpHound with `DCOnly` for a quieter
   pass), then `certipy find -vulnerable` for the AD CS half. Ingest both; the interesting paths
   usually start at an edge you do not own yet.
3. **Rank edges by prerequisite cost.** From `get writable`, split into: (a) no extra prerequisite
   — WriteDACL→DCSync, ForceChangePassword, group self-add; (b) needs a side effect on the target —
   SPN write for targeted Kerberoasting, `DONT_REQ_PREAUTH` for AS-REP; (c) needs infrastructure —
   GPO link edit (SYSVOL write), ADIDNS wildcard, share drop (needs a listener).
4. **Branch by what the environment allows:**
   - SPN write edge → finish in `active-directory-kerberos` (targeted Kerberoasting).
   - GPO write edge → `group-policy-objects.md`; if the GPO is linked to an OU, prefer an immediate
     task scoped to one computer over a domain-wide logon script.
   - `msDS-RevealOnDemandGroup` writable on an RODC → `rodc.md`.
   - MAQ > 0 and LDAP/SMB signing weak → `active-directory-lateral-movement` (RBCD / relay).
   - Writable share with live users → `shares.md` hash farming, then crack.
   - Name-resolution gap (LLMNR/NBNS/WPAD) → `adidns.md` before falling back to poisoning.
5. **Read secrets only after the graph is mapped.** Hand off to `active-directory-credentials` for
   NTDS/DCSync, LAPS, GMSA, dMSA, shadow credentials.
6. **Check the trust boundary.** If `Get-NetForestDomain`/`Get-ADTrust -Filter *` shows child or
   forest trusts, continue in `active-directory-domain-escalation`.

## Gotchas

- `-c all` in SharpHound **does not include `GPOLocalGroup`**; add it explicitly or you will miss
  local-admin-via-GPO edges.
- `adminCount=1` is set on privileged-group membership but never unset automatically. Those objects
  also have ACE inheritance from parent OUs disabled — an OU-wide `FullControl` grant will not
  reach them.
- AdminSDHolder ACLs are re-applied by `SDProp` roughly hourly. Any ACL you write on a protected
  object may be reverted, and a user removed from Domain Admins can reappear.
- GPO changes need a refresh: clients pull every 90 minutes ±30, or `gpupdate /force` locally.
  Immediate tasks run once per GPO refresh, not once per system.
- The "GenericWrite → RCM" path (`msTSInitialProgram`) only works on Terminal Servers/RDSH and is
  disabled by default on Windows newer than 2016 — it needs a registry change to re-enable.
- ADIDNS changes take ~180 seconds to replicate into DNS answers; a wildcard added now will not
  resolve instantly. Dynamic updates work unauthenticated only when the zone is Nonsecure and
  Secure; Secure Only requires a Kerberos ticket.
- Deleted objects default to 180-day retention and only Domain Admins can list/restore them unless
  explicit rights were delegated. Restoring can bring back attributes (including secrets) that
  were supposedly removed.
- Kerberos fails on >5 minutes clock skew; detect with `nmap --script smb2-time` before debugging
  anything else.
- Collection is loud: SharpHound LDAP queries and `--rid-brute` sweeps are high-volume and
  detectable. `DCOnly` collection and ADExplorer snapshots (legitimately Microsoft-signed) are the
  quieter options the corpus documents.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the
agreed scope. ACL and GPO writes are destructive to domain state — confirm the rules of engagement
before modifying objects, and revert changes you make.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
