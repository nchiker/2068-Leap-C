import json, collections, sys
# Part of the 2068-Leap-C feasibility study (component classification, docs/C_FEASIBILITY_STUDY.md section 1-2).
# Run: python3 romdeps.py <V2 build dir with test_basic.lst/exrom.lst> > deps.json; python3 classify.py deps.json
d = json.load(open(sys.argv[1]))
R = {r["name"]: r for r in d["routines"]}
BASIC = {"exrom_v2_compiler.asm","exrom_v2_symtab.asm","exrom_v2_vm_core.asm","v2_saveall.asm","v2_saveall_crc.asm",
         "v2_session_undo.asm","exrom_v2_shell.asm","exrom_v2_arrstore.asm","v2_lowrom_fill.asm",
         "v2_home.asm","v2_exrom.asm"}
isB = lambda n: R[n]["file"] in BASIC
out = collections.defaultdict(set); inn = collections.defaultdict(set)
for a, b, n in d["edges"]:
    out[a].add(b); inn[b].add(a)
print("== platform -> BASIC edges ==")
for a in sorted(R):
    if not isB(a):
        bs = sorted(b for b in out[a] if isB(b))
        if bs: print(f"  {R[a]['file']}:{a} -> " + ", ".join(f"{R[b]['file'].replace('.asm','')}:{b}" for b in bs))
print("== platform routines by caller class ==")
cls = collections.defaultdict(lambda: collections.Counter())
lists = collections.defaultdict(list)
for n, r in R.items():
    if isB(n): continue
    callers = inn[n]
    pc = any(not isB(c) for c in callers); bc = any(isB(c) for c in callers)
    k = "platform+basic" if pc and bc else "platform-only" if pc else "basic-only" if bc else "no-static-ref"
    cls[r["file"]][k] += r["size"]; lists[(r["file"], k)].append((n, r["size"]))
for f in sorted(cls): print(f"  {f:24s}", dict(cls[f]))
for (f, k), v in sorted(lists.items()):
    if k in ("basic-only", "no-static-ref"):
        print(f"  [{k}] {f}: " + ", ".join(f"{n}({s})" for n, s in sorted(v)))
print("== BASIC-file routines referenced by platform ==")
for n in sorted(R):
    if isB(n):
        pcs = sorted(c for c in inn[n] if not isB(c))
        if pcs: print(f"  {R[n]['file']}:{n}({R[n]['size']}) <- " + ", ".join(pcs))
