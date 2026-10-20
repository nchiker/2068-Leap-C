#!/usr/bin/env python3
"""RAM canary and banking invariants over the whole corpus (project_plan.md section 6, Phase 4).

Modelled on V2's tools/qual/qcanary.py (copied idea, not code). Every case of the corpus is compiled
(and the executable ones run) on the production ROM with the memory guards of tools/memguard.py:
  - the RAM canary: nothing the compile or the run may not write changes (the Leap-C cell area's
    tail, the V2 platform cells at $F180-$F3FF, $FF04-$FFFF, each image region's gap between its
    code and its data), the stack stays in $F800-$FEFF, the source is unchanged;
  - the banking invariants: never the stack in chunk 6, the paging depth 0 while a program runs
    (outside the EXROM trampolines' NOBRK sections), never a write to chunk 6 while the EXROM is
    paged in (compile: the EXROM-resident constant folding and library-name search; run: beep()'s
    trampoline; and the IM 1 handler throughout).
Executable cases (tests/{expr,...,mem}) are checked against their own expectations as well; the
declaration cases (tests/decl) are compiled only (CC_PROGRAM: E_NOMAIN is expected and ignored).

Writes build/canary.json (one record per case) and prints a summary; exit status 1 on any hit,
violation or failure.

Usage: canary.py [--workers 4] [--port 10800] [--only SUBSTR]
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
EXEC_DIRS = ("expr", "experr", "golden", "run", "stmt", "stmterr", "pp", "pperr", "lib", "rt", "mem")


def corpus(only=None):
    cases = []
    for d in EXEC_DIRS + ("decl",):
        cases += sorted(glob.glob(os.path.join(ROOT, "tests", d, "**", "*.c"), recursive=True))
    return [c for c in cases if not only or only in c]


def worker(port, paths, outq):
    import c2src
    import exectest
    import memguard
    from lcharness import Machine
    m = Machine(os.path.join(ROOT, "build"), port)
    m.start()
    try:
        for p in paths:
            rel = os.path.relpath(p, ROOT)
            rec = dict(case=rel)
            try:
                if rel.split(os.sep)[1] == "decl":
                    lines = c2src.lines_of(open(p, encoding="latin-1").read())
                    r = exectest.compile_and_run(m, lines, run=False, invariants=True, canary=True)
                    msgs = []
                    if not r.compile_ok:
                        msgs.append("compile did not return")
                    msgs += ["banking invariant violated: " + v for v in r.violation]
                    msgs += ["canary: the %s wrote %s %s-%s (%d bytes)" % (h["phase"], h["span"], h["first"],
                                                                           h["last"], h["bytes"])
                             for h in r.canary_hits if not h.get("allowed")]
                    rec.update(ok=not msgs, msg="; ".join(msgs), stack_lows=r.stack_lows,
                               canary=r.canary_hits, violation=r.violation)
                else:
                    ok, msg, info = exectest.check_case(m, p, guards=True)
                    rec.update(ok=ok, msg=msg, stack_lows=info["stack_lows"] if info else {},
                               canary=info["canary"] if info else [], violation=info["violation"] if info else [])
            except Exception as e:                       # a harness failure: restart the emulator
                rec.update(ok=False, msg="harness: %r" % e)
                try:
                    m.stop()
                except Exception:
                    pass
                m = Machine(os.path.join(ROOT, "build"), port)
                m.start()
            outq.put(rec)
    finally:
        m.stop()
        outq.put(None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--port", type=int, default=10800)
    ap.add_argument("--only")
    ap.add_argument("--json", default=os.path.join(ROOT, "build", "canary.json"))
    a = ap.parse_args()
    t0 = time.time()
    cases = corpus(a.only)
    n = max(1, min(a.workers, len(cases)))
    q = mp.Queue()
    ps = [mp.Process(target=worker, args=(a.port + w, cases[w::n], q)) for w in range(n)]
    for p in ps:
        p.start()
    recs, done = [], 0
    while done < n:
        r = q.get()
        if r is None:
            done += 1
            continue
        recs.append(r)
        if not r["ok"]:
            print("canary: FAIL %s: %s" % (r["case"], r["msg"]), flush=True)
    for p in ps:
        p.join()
    recs.sort(key=lambda r: r["case"])
    bad = [r for r in recs if not r["ok"]]
    lows = {ph: [r["stack_lows"][ph] for r in recs if r.get("stack_lows", {}).get(ph) is not None]
            for ph in ("compile", "run")}
    allowed = [r["case"] for r in recs for h in r.get("canary", []) if h.get("allowed")]
    summary = dict(cases=len(recs), failures=len(bad), wall_s=round(time.time() - t0, 1),
                   stack_low_compile="$%04X" % min(lows["compile"]) if lows["compile"] else None,
                   stack_low_run="$%04X" % min(lows["run"]) if lows["run"] else None,
                   hires_display_writes=sorted(set(allowed)))
    with open(a.json, "w") as f:
        json.dump(dict(summary=summary, cases=recs), f, indent=1)
    print("canary: %d cases (%d declaration cases compiled only), %d failures; lowest stack byte: compile %s, "
          "run %s; display file 2 written in hi-res mode by %d cases; %.0f s" % (
              len(recs), sum(1 for r in recs if os.sep + "decl" + os.sep in r["case"]), len(bad),
              summary["stack_low_compile"], summary["stack_low_run"], len(set(allowed)), summary["wall_s"]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
