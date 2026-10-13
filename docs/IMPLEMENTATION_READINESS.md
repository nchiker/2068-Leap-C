# 2068-Leap-C — Implementation Readiness

**2026-10-12.** Feasibility is closed. Implementation can start with milestone **M1.1** (`project_plan.md` §3).

## Ready

| Input | State |
|---|---|
| Architecture | Approved (`spec.md` §1-5): separate Leap-C ROM; on-machine single-pass Small-C-style compiler; native Z80; shared HOME-ROM helpers; mixed templates by default; floating point optional/later; cross-compilation as a development tool only |
| Specification | `spec.md` v0.1: language subset, ABI, templates, ROM budgets per bank, memory map (baseline), library, storage, BREAK, errors |
| Plan | `project_plan.md` v0.1: 10 phases. Every milestone has assembled-size and executable-test completion criteria. Budget overruns follow an engineering protocol, not a feasibility restart |
| Measured baselines | Reclaimable ROM, per-component V2 sizes, template code shapes and helper costs, chunk-6 execution and banking rules, runtime RAM (all in `docs/C_FEASIBILITY_STUDY.md` rev 3) |
| Reusable assets | V2 platform sources (frozen tag, to be vendored). V2 harness and layout-guard designs. The spike's template byte sequences (golden references for M1.3) and helper core (92 B) |
| Tools | sjasmplus, ZEsarUX 13.0, ts2068-debug/ZRCP, Python, the z80-skills methods. Nothing further needs installing for Phase 1 |
| Chunk-6 loading problem | Resolved in design (`spec.md` §8.3): source never loads into chunk 6; block I/O moves to HOME in Phase 7 (net 0 ROM), with staged loading as the fallback |

## Owner decisions needed

None of these blocks M1.1.

| # | Decision | Recommended default | Needed by |
|---|---|---|---|
| 1 | Key positions for `[ ] { } \| ~ ^ \` (do they match the physical TS2068 legends?) | SYMBOL SHIFT + Y U F G S A H D (`spec.md` §6.2) | Phase 5 |
| 2 | Leap-C tape identity: version word `$8C00`, mutual refusal with V2 BASIC tapes | adopt | Phase 7 |
| 3 | Repository: local `git init` at M1.1; GitHub remote, name and publication | local git now; remote later | M1.1 (local) / any time (remote) |
| 4 | ROM reserve floors at release | HOME 512 B, EXROM 256 B | before Phase 10 |
| 5 | Floating point: Release 1 or later (the calculator is retained either way) | later; decide at the Phase 8 decision point | Phase 8 |
| 6 | Physical hardware validation: TS2068, EPROM programming, cassette deck, who runs the checklist | — | Phase 9 |
| 7 | Optional SDCC installation as a test oracle | not needed for Phases 1-2 | if requested |

**Not owner decisions** (engineering choices recorded in the plan):

- system-variable relocation (decided by the M1.1 boot test, with a documented fallback);
- the exact RST map (confirmed from corpus frequencies in Phase 2);
- the BREAK implementation detail (Phase 3).

## Main risks (managed in implementation)

1. **HOME ROM pressure.** The compiler is estimated at 6.9-10.8 KB. It is measured every milestone and handled by the budget protocol (`project_plan.md` §1.2).
2. **Compile speed:** target ≤ 25 ms per line, measured from M1.1.
3. **BREAK unwind safety:** a full BREAK test matrix in Phase 3.
4. **Real-hardware timing and contention:** measured in Phase 9.

## Recommended first milestone

**M1.1 — Foundation and lexer.**

- **Deliverables:** git init; `platform/` vendored from the V2 tag with a delta check; Leap-C HOME/EXROM images that boot (BASIC removed, baseline memory layout); `make`/`make budget`/`make check`/`make test`; `tools/lcharness.py`; the C lexer and source streaming.
- **Completion:** reproducible images; boot test; ≥ 60 lexer cases; lexer size against its 1,100-byte budget; lexer throughput measured.

The step after this report is writing and testing that code.
