# Active Directory Enumeration and Recon (active-directory-enumeration)

References: 11 | tokens ~19268

| # | ref | title | lines | ~tokens | key sections |
|---|-----|-------|-------|---------|--------------|
| 1 | `domain-enumeration.md` | Active Directory - Enumeration | 428 | 4416 | Using BloodHound; Using PowerView; Using AD Module; User Hunting; RID cycling; Other Interesting Commands; References |
| 2 | `groups.md` | Active Directory - Groups | 177 | 1680 | Dangerous Built-in Groups Usage; AdminSDHolder Attribute; DNS Admins Group; Schema Admins Group; Backup Operators Group; References |
| 3 | `acl-ace.md` | Active Directory - Access Controls ACL/ACE | 370 | 3706 | GenericAll/GenericWrite; WriteDACL; WriteOwner; ReadLAPSPassword; ReadGMSAPassword; ForceChangePassword; Organizational Units ACL; References |
| 4 | `group-policy-objects.md` | Active Directory - Group Policy Objects | 165 | 2025 | Find vulnerable GPO; Abuse GPO with SharpGPOAbuse; Abuse GPO with PowerGPOAbuse; Abuse GPO with pyGPOAbuse; Abuse GPO with PowerView; Abuse GPO with StandIn; Abuse GPO with GroupPolicyBackdoor; References |
| 5 | `ad-from-linux.md` | Active Directory - Linux | 233 | 2203 | CCACHE ticket reuse from /tmp; CCACHE ticket reuse from keyring; CCACHE ticket reuse from SSSD KCM; CCACHE ticket reuse from keytab; Extract accounts from /etc/krb5.keytab; Extract accounts from /etc/sssd/sssd.conf; Extract accounts from SSSD keyring; SSH GSSAPI |
| 6 | `machine-account-quota.md` | Active Directory - Machine Account Quota | 48 | 805 | Machine Account Quota Process; References |
| 7 | `recycle-bin.md` | Active Directory - Recycle Bin | 84 | 755 | Details; Deleted Objects; Restore Objects; References |
| 8 | `rodc.md` | Active Directory - Read Only Domain Controller | 70 | 895 | RODC Golden Ticket; RODC Key List Attack; RODC Computer Object; References |
| 9 | `adidns.md` | Active Directory - Integrated DNS - ADIDNS | 82 | 800 | LDAP-Based (Require authentication); Dynamic Updates (Doesn't require authentication); DNS Reconnaissance; References |
| 10 | `shares.md` | Internal - Shares | 182 | 1537 | READ Permission; WRITE Permission; References |
| 11 | `tricks.md` | Active Directory - Tricks | 40 | 446 | Kerberos Clock Synchronization; References |
