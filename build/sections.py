import re, sys, json, pathlib
def sections(p):
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    fence = False; out=[]
    for i,l in enumerate(lines,1):
        s=l.strip()
        if s.startswith('```') or s.startswith('~~~'):
            fence = not fence; continue
        if fence: continue
        m = re.match(r'^(#{1,3})\s+(.*)', l)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()[:90]))
    return out, len(lines)
for f in sys.argv[1:]:
    p=pathlib.Path(f); secs,n=sections(p)
    print(f"##### {f}  ({p.stat().st_size//1024}KB, {n} lines, {len([s for s in secs if s[1]==2])} H2)")
    for ln,lvl,t in secs:
        if lvl<=2: print(f"  {ln:5d} {'#'*lvl} {t}")
    print()
