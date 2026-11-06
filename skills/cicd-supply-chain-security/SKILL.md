---
name: cicd-supply-chain-security
description: >-
  Assess CI/CD pipelines and the software supply chain: GitHub Actions, GitLab CI, Azure DevOps,
  CircleCI, Buildkite, Drone CI runner abuse, hardcoded secret enumeration, and
  package-manager/build-file credential attacks (npm, NuGet, PyPI). Use when an engagement
  includes source control or CI/CD, when you find pipeline configuration or tokens, or when
  reviewing build-system security.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "9"
  generated-by: build/build.py
---

# CI/CD and Supply Chain Security

A CI/CD system is three questions stacked: does the pipeline build untrusted input (a fork, an issue, a PR), where does the job execute (hosted runner, self-hosted runner, shell executor on a shared box), and what can that job reach (secrets, cloud credentials, the cluster it deploys to). Poisoned Pipeline Execution is the case where you control a file the pipeline executes and the trigger fires on your input. Start at the platform overview, then branch to the platform file - the config path tells you which one you are in.

## When to use this skill

- Source control or CI/CD is in scope, or you have found workflow/pipeline configuration in a repository.
- You have a pipeline token, PAT, SCM session cookie, or run logs, and need the secrets behind them.
- You want to test whether a fork pull request can execute code in the target's CI.
- You are reviewing build-system security: runner isolation, hardcoded secrets, build-file injection.
- Not this skill: the cloud account the pipeline deploys into → `aws-security` / `azure-entra-security`; Azure DevOps identity recon and PAT persistence → `azure-entra-security`; the cluster the runner sits in → `container-security`.

## First moves

1. Read `cicd-overview.md` first if the platform is unknown; it is the index that routes to each per-platform file. Then identify the platform from the config path alone:

```text
.github/workflows/*.yml      GitHub Actions
.gitlab-ci.yml               GitLab CI
azure-pipelines.yml          Azure DevOps
.circleci/config.yml         CircleCI
.buildkite/*.yml             Buildkite
.drone.yml                   Drone CI
```

2. Establish whether the trigger includes untrusted input. In GitHub Actions that is `pull_request` (and `workflow_dispatch` is a manual trigger, not an external one); in Azure Pipelines look for `pr:`; in CircleCI forked PR builds are opt-in:

```yaml
on:
  pull_request
```

3. Scan the repository for pipeline misconfiguration before exploiting anything - reachability, dangerous triggers and secret exposure in one pass:

```bash
poutine analyze_local .
poutine -token "$GH_TOKEN" analyze_repo messypoutine/gravy-overflow
poutine -token "$GH_TOKEN" analyze_org messypoutine
```

4. Enumerate self-hosted runners for the organisation; a non-ephemeral runner is a persistent execution target:

```bash
gato -s enumerate -t targetOrg -oJ target_org_gato.json
gato e --repository vercel/next.js
# "The repository contains a non-ephemeral self-hosted runner!" = long-lived target
```

5. List the secrets the pipeline stores before trying to extract them - the inventory tells you whether it is worth a pipeline:

```bash
nord-stream.py devops --token "$PAT" --org myorg --list-secrets
```

6. Extract them by deploying a malicious pipeline, with the build file type matching the service connection you want:

```bash
nord-stream.py devops --token "$PAT" --org myorg
nord-stream.py devops ... --build-yaml test.yml --build-type ssh
```

7. Hunt hardcoded credentials across the SCM itself, which needs no pipeline access at all:

```powershell
SCMKit.exe -s gitlab -m searchcode -c apikey -u https://gitlab.something.local -o "some search term"
SCMKit.exe -s gitlab -m searchfile -c userName:password -u https://gitlab.something.local -o "some search term"
SCMKit.exe -s gitlab -m listrepo -c apikey -u https://gitlab.something.local
```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [cicd-overview.md](references/cicd-overview.md) | **start here** - platform not yet known | PPE definition, tool list (gato, Gato-X, SCMKit, octoscan, poutine, nord-stream, glato), links to every platform file plus secrets and build-file chapters |
| [github-actions.md](references/github-actions.md) | `.github/workflows/` exists | default actions, `pull_request` and `workflow_dispatch` triggers, misconfigured action scanning, repository hijacking, `${{ github.event.issue.title }}` injection, secrets/variables contexts, self-hosted runner enumeration and ephemeral vs non-ephemeral |
| [gitlab-ci.md](references/gitlab-ci.md) | `.gitlab-ci.yml` exists | runner registration, command-execution job with a runner matrix, executor risk (shell vs docker vs ssh), CI/CD variables, PAT/SSH-key persistence, user promotion, SCMKit |
| [azure-devops.md](references/azure-devops.md) | `azure-pipelines.yml` exists | `pr:` trigger, secret extraction per service connection (AzureRM, GitHub, AWS, SonarQube, SSH) with nord-stream |
| [circleci.md](references/circleci.md) | `.circleci/config.yml` exists | fork PR builds are opt-in by default; `run` step is the execution primitive |
| [buildkite.md](references/buildkite.md) | `.buildkite/*.yml` exists | `command` step; runners are usually self-hosted, so the blast radius includes the hosting cluster/cloud |
| [drone-ci.md](references/drone-ci.md) | `.drone.yml` exists | `commands` step; self-hosted runners as above |
| [secrets-enumeration.md](references/secrets-enumeration.md) | you have SCM access and want credentials without touching CI | SCMKit repo/code/file/snippet search across GitHub and GitLab |
| [package-managers.md](references/package-managers.md) | you can submit a change and the pipeline builds PRs | CI-agnostic build-file injection: `package.json` scripts, `setup.py`, `*.sh`, Maven/Gradle wrappers and `pom.xml`, `BUILD.bazel`, `Makefile`, `Rakefile`, `*.csproj` |

## Workflow

1. **Platform.** Unknown → `cicd-overview.md`. Known → straight to the platform row above. The config file path is the classification; there is no ambiguity once you have the repo.
2. **Trigger.** Does the pipeline run on forked PRs or untrusted issues? GitHub `on: pull_request`, Azure `pr:`, CircleCI opt-in forked builds. If it does not, Poisoned Pipeline Execution is off the table and the path is credentials or runner compromise instead.
3. **Execution surface.** Hosted runner → the job is isolated, so aim at the secrets and cloud credentials the workflow passes in. Self-hosted → `github-actions.md` `gato` enumeration; GitLab shell executor runs jobs as the runner's user and can read other projects' code; Buildkite and Drone are commonly self-hosted, so the escape is into the Kubernetes cluster or cloud account that hosts them.
4. **Injection.** With a PR-triggered build, inject into whatever the pipeline executes: a `run` step that interpolates attacker input (`${{ github.event.issue.title }}`) for GitHub, or a build file from `package-managers.md` (`preinstall`/`install`/`build`/`test` in `package.json`, `setup.py`, `.sh`, `pom.xml`, `*.csproj`) when you do not know which CI builds the repo.
5. **Secrets.** `secrets-enumeration.md` for hardcoded material in the SCM; `nord-stream` for pipeline-stored secrets (GitHub/GitLab/Azure DevOps); `gh-hijack-runner` to fake a runner and leak jobs. Enumerate before extracting.
6. **Persist and pivot.** A PAT or SSH key created through the SCM API (`gitlab-ci.md`, and the ADO endpoints in `azure-entra-security`) outlives the pipeline run. Cloud credentials from a job go to `aws-security` / `azure-entra-security`; a runner inside a cluster goes to `container-security`.

## Gotchas

- CircleCI does **not** build forked pull requests by default - it is an opt-in feature of the pipeline owner, so check before planning a fork-PR attack.
- GitHub blocks registration of a previous repository name that had 100 clones in the week before the rename or the owner-account deletion, which limits repository hijacking; a non-existent `uses:` owner is still worth checking, just not instantly claimable.
- `workflow_dispatch` is a manual trigger, not an untrusted one. A workflow with only `workflow_dispatch` and `push` is not PR-exploitable.
- The GitLab **shell executor** runs jobs as the runner's user and can read code from other projects built on the same host; the **docker** executor is safe in non-privileged mode; the **ssh** executor is MITM-prone because it omits `StrictHostKeyChecking`.
- GitLab CI/CD variables are explicitly less secure than a secrets-management provider - do not treat a pipeline variable as a safe place for a credential.
- Build-file payloads are CI-agnostic, but the escaping is not: JSON escaping for `package.json`, XML escaping for `pom.xml` and `*.csproj`, backslash doubling inside `BUILD.bazel`.
- Maven and Gradle injection prefers the wrappers (`mvnw`, `gradlew`, `mvnw.cmd`, `gradlew.bat`) because they are plain executable scripts; the `pom.xml` plugin route is the fallback when the wrappers are absent.
- Secrets inside a GitHub Actions job are only exposed to steps that receive them via `env:`/`secrets:` context - a compromised build step sees what the workflow passes, not everything in the repository.
- Azure DevOps secret extraction is per service-connection type (AzureRM, GitHub, AWS, SonarQube, SSH) - match `--build-type` to the credential you want, e.g. `--build-type ssh`.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the agreed scope. Pushing malicious build files to a live repository changes real artifacts - use a fork or a lab unless the engagement explicitly permits it.

## Source

Converted from the upstream InternalAllTheThings CI/CD guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
