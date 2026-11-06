# Active Directory Lateral Movement, Relay and Coercion (active-directory-lateral-movement)

References: 4 | tokens ~10391

| # | ref | title | lines | ~tokens | key sections |
|---|-----|-------|-------|---------|--------------|
| 1 | `ntlm-relay.md` | Internal - NTLM Relay | 454 | 5118 | MS08-068 NTLM reflection; LDAP signing not required and LDAP channel binding disabled; SMB Signing Disabled and IPv4; SMB Signing Disabled and IPv6; Drop the MIC - CVE-2019-1040; Drop the MIC 2 - CVE-2019-1166; Ghost Potato - CVE-2019-1384; RemotePotato0 DCOM DCE RPC relay |
| 2 | `kerberos-relay.md` | Internal - Kerberos Relay | 116 | 1846 | Kerberos Relay over HTTP; Kerberos Relay over DNS; Kerberos Relay over SMB; Kerberos Reflection - CVE-2025-33073; References |
| 3 | `coercion.md` | Internal - Coerce | 153 | 1896 | Signing; WebClient Service; MS-RPRN - PrinterBug; MS-EFSR - PetitPotam; MS-DFSNM - DFS Coercion; MS-WSP - WSP Coercion; References |
| 4 | `dcom.md` | Internal - DCOM | 120 | 1531 | DCOM via MMC Application Class; DCOM via Office; DCOM via ShellExecute; DCOM via ShellBrowserWindow; References |
