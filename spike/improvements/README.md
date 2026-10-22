# Prototypes of the recommended improvements (after Phase 9)

These are the prototypes measured for the improvements report (https://claude.ai/artifact/LvHLDsfAKnLLKhaQ33ckdj). Each fix is one patch. They apply in order, with `patch -p1` from the repository root, to the Phase 9 tree with platform delta D14.

| Patch | Fix | HOME B | EXROM B |
|---|---|---:|---:|
| `fix1-cond-float-int.patch` | `?:` with a float arm and an integer arm converts the integer (C89 6.3.15) | +55 | 0 |
| `fix2-error-names.patch` | errors 21, 22, 52, 70 and 76 name the identifier | +17 | +18 |
| `fix3-udiv-dead-branch.patch` | `RT_UDIV`'s unreachable branch removed (112 T less per division) | −5 | 0 |
| `fix4-exrom-dead-code.patch` | unreachable vendored EXROM code removed | 0 | −154 |
| `fix5-error-column.patch` | after a compile error, the cursor lands at the error's column (+2 B RAM) | 0 | +41 |
| `fix6-line-store-to-exrom.patch` | in reserve: `MEM_LINE_STORE` and its helpers assemble in the EXROM | −212 | +212 |

Measured with `tools/budget.py` on 2026-10-21:

- Phase 9: HOME 15,796 B (588 B free), EXROM 7,881 B (311 B free).
- With fixes 1-5: HOME 15,863 B (521 B free), EXROM 7,786 B (406 B free).
- With fixes 1-6: HOME 15,651 B (733 B free), EXROM 7,998 B (194 B free).

## What the patches do not include yet

- **Budget and docs:** no budget ledger entries, `spec.md` text or milestone report.
- **Fix 1:** `tests/float/err/cond_mixed.c` and `cond_mixed_int_first.c` now compile, so they must be retired in favour of the patch's positive test. The deviation in `spec.md` §4.9 must go too.
- **Fix 4:** the vendored files it changes are not yet recorded as platform deltas. Mark them in `platform/MANIFEST` (D15 onward), describe them in `platform/UPSTREAM.md`, then run `tools/check_platform.py --update`. Until then, `make check` fails. `beep()` and `sound()` are unchanged by design: `LIB_SOUND`, `SOUND_EXROM`, `AY_BEEP_PERIOD` and `AY_BEEP_PLAY` stay.
- **Fix 5:** the shell case `D4-typed-run-path` still expects the cursor at column 0. It is now at column 14, on the error's token, so the expectation needs updating.
- **Fix 6:** its comment in `memory.asm` cites "D11, D14", but D14 is now the bank switch's delta, so it needs renumbering. Phase 10's owner decisions make Fix 6 optional.

## Test results of the prototypes

- **Fixes 1-4:** shell suite 43/43, cassette suite all pass, workflow typed and report cases all pass. Each fix's own new tests and the affected corpus directories pass.
- **Fixes 1-6:** shell suite 42/43 and the corpus through `RUN` 884/886. All three failures are the intended changes listed above: `D4-typed-run-path` (Fix 5), and `cond_mixed.c` and `cond_mixed_int_first.c` (Fix 1).

`PHASE10_PROMPT.md` is the owner's approval prompt for the phase that applies fixes 1-5 and adds library loading.
