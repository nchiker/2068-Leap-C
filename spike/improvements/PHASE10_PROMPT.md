Phase 10 approval: recommended fixes and library loading

Approved: implement and qualify Phase 10 of 2068-Leap-C (the TS2068 C ROM). This phase goes in before documentation and release qualification. Update project_plan.md so that documentation and release qualification becomes Phase 11.

Baseline: the Phase 9 commit, spec.md v0.11 and docs/milestones/M9.md. The designs and measured costs are in the improvements report: https://claude.ai/artifact/LvHLDsfAKnLLKhaQ33ckdj. Read it first. Its prototypes are in spike/improvements/: one patch per fix, applied in order, with a README listing what each still needs. Start from them, and treat the measured sizes as targets to meet or beat.

Scope

1. Fixes 1-5 from the report, each at its smallest:
   - Fix 1: in `?:` with one float arm and one integer arm, the integer arm is converted to float (C89 6.3.15), reusing CX_TOFLT. A pointer or void arm with a float arm stays TYPE MISMATCH. Retire tests/float/err/cond_mixed.c and cond_mixed_int_first.c in favour of positive tests, and remove the deviation from spec.md §4.9.
   - Fix 2: errors 21, 22, 52, 70 and 76 name the identifier on the status row, as error 23 does. For 70 and 76, UNDEF_CHECK sets NM from the symbol. An empty name, as for a #define, shows no name.
   - Fix 3: remove RT_UDIV's unreachable branch.
   - Fix 4: remove the unreachable vendored EXROM code the report lists. Record it as new platform deltas, D15 onward, in platform/UPSTREAM.md, MANIFEST and deltas/. beep() and sound() must not change: LIB_SOUND, SOUND_EXROM (the chime), AY_BEEP_PERIOD and AY_BEEP_PLAY stay.
   - Fix 5: after a compile error, the cursor lands at the error's column. Update the tests that expect column 0, such as the shell case D4-typed-run-path.

2. Library loading: Stage 1 of the report's plan, with V2-style jump-table slots.
   - Image: a library is an assembly image for image region 3 ($F400-$F7FF, 1 KB). It holds a header (magic, ABI version, export count), then an export table in LIB_NAMES's record format (name, address, signature byte), then code and data.
   - Jump table: ROM services are reached through a fixed jump table in HOME. Make it V2-style: 16 slots of `jp`, 48 B, at an address that never moves, guarded by an ASSERT. Choose the services a library needs, for example character and string output, the heap, the integer and float helpers, the runtime error exits, and key and frame reads. Document each slot in spec.md. Never reorder slots, and keep unused slots reserved. Give no slot to the editor engine, because Fix 4 assumes the shell's hooks are always set.
   - Tools: tools/lib2tape.py builds a library's .tap, .tzx and .wav from an sjasmplus source and an ABI include (for example include/leapc_lib.inc) that defines the header and the slot addresses.
   - Shell: `LIB "name"` loads a library through the existing tape path. It refuses a wrong magic or ABI version before storing a byte, records the export table, and reports `LIBRARY name: n FUNCTIONS`. `LIB` alone unloads the library; a reset clears it. Decide and document whether NEW and LOAD keep it.
   - Compiler: while a library is loaded, region 3 is closed to program images, as #pragma hires closes region 4. An identifier that no declaration names is looked up in the ROM's table and then the library's, with the same binding code, and calls are type-checked from the signature byte. Define and test what happens when a library exports a name the ROM also has.
   - Runtime: BREAK, runtime errors and the canary must behave inside library code as they do inside the ROM's library code.
   - Deliverables: ship at least one example library (source and tapes) that the tests use and the docs describe. Add a library tape and a check program to the hardware kit and to docs/HARDWARE_CHECKLIST.md.
   - Out of scope: Stage 2, C libraries compiled on the machine (#pragma library, SAVE "name" LIB).

Owner decisions

- Library loading uses V2-style jump-table slots, not just an identity word, so that libraries built against the slot table keep working across ROM updates that keep the slots.
- The reserve floors may be lowered as far as this phase needs, but not below 128 B in either ROM. With the ROM feature-complete, the reserve only has to cover defects found in release qualification and on real hardware. Record each change as a budget.toml ledger entry.
- Fix 6, moving the line store to the EXROM, is not required. Use it only if HOME would otherwise fall below 128 B free.

Authority and constraints

- You have authority to debug, fix, optimise, refactor, relocate ROM code and adjust budgets. Preserve all approved functionality and test coverage. Every fix and feature gets tests that fail without it.
- Do not modify the frozen ~/2068-Leap project; read only its tag.
- Do not begin documentation and release qualification (Phase 11).
- Do not stop at an investigation, test plan or partial report. Complete the phase autonomously, stopping only for a genuinely unavoidable owner decision.
- Use lower-cost models for routine test runs and actions you direct, with the results always coming back to you.

Qualification and closing

- On the final images, run the full Phase 9 qualification:
  - make qualify: make test with ROM coverage, make fuse including the frames case, make timing, the --ram warm and --ram random:7 suites, make capacity, the hardware kit's verification with its 30-minute soak, and make check;
  - then make repro.
- Exercise library loading on both ZEsarUX (real tape signal) and Fuse.
- Update spec.md (v0.12), the budget ledger and project_plan.md. Write docs/milestones/M10.md. Then commit and push to the private GitHub backup (origin nchiker/2068-Leap-C).
