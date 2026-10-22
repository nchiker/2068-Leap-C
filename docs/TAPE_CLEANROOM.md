# Clean-room record: the tape block I/O and the block-graphics glyph (Phase 11, M11-tape)

This document records how Leap-C's cassette block routines (`TAPE_SEND_BLOCK`, `TAPE_RECV_BLOCK` in
`src/runtime/tapeblock.asm`) and the block-graphics glyph (`GFX_CHAR_TO_FONT_OFFSET.is_block_graphics` in
`platform/kernel/graphics/graphics.asm`, platform delta D21) were written, so that it can be shown that they
contain nothing derived from the stock TS2068 / ZX Spectrum ROM (Amstrad copyright). They replace V2's port of
the stock SA-BYTES / LD-BYTES and V2's glyph generator, which contained the stock PO-GR-2 sequence (`NOTICE` §3).

The work was done on 2026-10-22 by AI agents (Claude, Anthropic) directed by the project owner's approved prompt
(the "option C" of `docs/milestones/M11-beta.md` §2, A8). Each author was a fresh agent with no context but its
prompt. The three prompts are reproduced in full below; the messages sent to the authors while they worked, abridged.

## 1. The method

| Stage | Author | Output | Inputs allowed | Inputs forbidden |
|---|---|---|---|---|
| A, the specification | a fresh agent (Claude Opus) | `docs/TAPE_SIGNAL_SPEC.md` | public descriptions of the cassette format (the TZX format's documentation, general descriptions of the signal); Leap-C's own documents; the old routines' **contract headers** and their **callers** only (`storage.asm` lines 107-187, 236-257, 372-401, 599-1062 at `6201aa2`); the tests and the harness; the description of Fuse's loader detection given by the orchestrator (§3) | the old routines' bodies (`storage.asm` lines 1-106, 188-235, 258-371, 402-598) and their git history; the stock ROMs; any ROM disassembly; the frozen V2 repository; Fuse's `loader.c` |
| B, the tape routines | a second fresh agent (Claude Opus) | `src/runtime/tapeblock.asm` | `docs/TAPE_SIGNAL_SPEC.md`; Leap-C source outside `platform/kernel/storage/` (for integration and style); the tests and tools, which it could run (including running, not reading, the beta.1 images for the envelope comparison); the shrink-z80 skill (checked by the orchestrator to contain no tape code) | `storage.asm` in any form, `platform/deltas/`, the git history of `platform/`, the stock ROMs, any disassembly (of them or of the beta.1 images), the V2 repository, Fuse's `loader.c`, the web |
| B, the glyph | a third fresh agent (Claude Sonnet) | the body of `.is_block_graphics` | a description of the glyph from the screen format (bit 0 top-right quarter, bit 1 top-left, bit 2 bottom-right, bit 3 bottom-left) and the routine's contract at the label; the rest of `graphics.asm` | the old code (removed from the file before the agent started), the git history and deltas of `graphics.asm`, the stock ROMs, any disassembly, the V2 repository, the web |

The orchestrator (the main agent of the session) wrote no line of either routine. It wrote the prompts, the test
tools (`tools/tapetol.py`, `tools/provenance.py`, `tools/beta1ref.sh`), the harness changes (the new labels in
`tools/lcharness.py` and `tools/memguard.py`), the platform bookkeeping (deltas D20 and D21, the cut records,
`tools/check_platform.py`) and the documents, and it removed the old code from `platform/` before the Stage B
authors started (so their builds, listings and working tree never contained it).

**No old text in the new history.** None of the prompts, documents or commits of this phase contains the old
bodies. The platform patches of D20 and D21 would normally show the removed lines; instead
`platform/deltas/*.cut` records the removed upstream line ranges by their sha256 only, and the patches are
computed from the V2 tag's file without those ranges (`tools/check_platform.py` verifies both against the tag).

## 2. What each author reported having read

- **Stage A** (its final report): spec.md, project_plan.md, NOTICE, M7, M9, M10, M11-beta, EMULATORS.md,
  HARDWARE_CHECKLIST.md (parts); `storage.asm` only in the allowed ranges, as committed in `6201aa2`;
  `src/shell/tape.asm`, `src/rom/home.asm`, `src/rom/exrom.asm`, the tape part of `src/runtime/library.asm`,
  `platform/include/sysvars.inc` and `hardware.inc`, `platform/kernel/bank/bank.asm`, `include/*.inc`,
  `budget.toml`, the tape tests and harness. Web: the TZX format (worldofspectrum.net/TZXformat.html), the
  Sinclair wiki's "Spectrum tape interface" page, the World of Spectrum 48K reference FAQ. **Exposure it
  reported:** a repository-wide grep printed six lines from the forbidden ranges of `storage.asm`: two header
  comments naming the routines, the two routine labels, the test hook `IFDEF STORAGE_TEST_FAKE_RECEIVE` /
  `jp STORAGE_TEST_RECEIVE_BLOCK`, and a comment fragment. None is code taken from the stock ROM; the only fact
  used was that the test hook exists (and that no build defines it).
- **Stage B, tape** (its final report): the specification; `src/runtime/tapeblock.asm` (the placeholder),
  `src/rom/home.asm`, the heads of `src/runtime/rtexit.asm` and `helpers.asm` for the style; the
  `PORT_FE_SHADOW` and `STORAGE_ENTRY_RETRY` parts of `sysvars.inc`; `hardware.inc`, `leapc_layout.inc`,
  `budget.toml` (grep); the tools it ran (`lcharness.py`'s capture, `tapes.py`, `tapetest.py`, `tapetol.py`,
  `fusedrive.py`, `hwkit.py`); the shrink-z80 skill's SKILL.md, hard-contract, dispatcher, asm-micro and
  byte-evidence references; its own build outputs. No web page. It reported meeting no old tape code, and that it
  deliberately avoided a byte loop built on a sentinel bit, a structure it recognised as the stock ROM's.
- **Stage B, glyph** (its final report): the prompt; `graphics.asm` lines 385-485 (after the old code had been
  removed) and grep hits for the routine's labels; `BLOCK_GFX_SCRATCH` in `sysvars.inc`; its own build
  outputs.

## 3. The orchestrator's own exposure

Recorded so that nothing is left implicit:

- While locating the end of `STORAGE_RECEIVE_BLOCK`'s contract header, the orchestrator printed `storage.asm`
  lines 372-440, which include the first 38 lines of the old receiver's body (its entry: the shared exit, the
  stash of the flag, the port set-up, the retry budget), and a later grep printed four more lines of that body.
  It also read the file's old header (lines 1-106), the constants' names (not their values) and the contract
  headers. It never read the rest of either body, the old graphics sequence, or the stock ROMs' bytes (the
  provenance check prints offsets and lengths only).
- It read Fuse 1.9.1's `loader_detect_loader` (`loader.c` lines 404-447, GPL emulator code, not ROM code) and
  passed the rule it implements to Stage A in words (Stage A's addendum below); it did not read the part of
  `loader.c` that pattern-matches loader code.
- It wrote none of the new routines' code and reviewed them only after they were written. Its one request to
  the Stage B author after the first version (the border stripes, §5) named a behaviour, not code.

The authors are language models that may have seen public ROM disassemblies in their training. The controls
against that are the instructions (no recall of stock instruction sequences; the Stage B author reported
steering away from one recognised structure), the structure of the result (§4), and the byte comparison
(`tools/provenance.py`: no common run of 12 bytes or more with the stock 48K and TS2068 ROMs except
`SH_IDCHAR`'s, which is Leap-C's own and unrelated to the tape code).

## 4. The result

- `TAPE_SEND_BLOCK` 143 B (with `TS_HALF`), `TAPE_RECV_BLOCK` 173 B (with `TR_BYTE`, `TR_SEDGE`,
  `TR_EDGE`): 316 B against the old pair's 331 B; stack 28 B in `tape_load`'s worst case, as before. The
  glyph: 36 B against V2's 48 B.
- The design differs from the stock one throughout: one edge routine for the sender (`TS_HALF`: a `djnz` delay,
  the port image in A' toggled with `xor`), with per-place delay counts; a receiver that measures widths as
  differences of a free-running pass counter in B (each read of port $7FFE gives EAR and SPACE together), locks
  on 255 pilot half-pulses in a window, decides each bit on its full length against one threshold, and counts its
  silence budget in counter overflows. See the file's comments for every T-state count.
- Measurements, the tolerance envelope and the qualification: `docs/milestones/M11-tape.md`.

## 5. The prompts

### 5.1 Stage A

    You are the Stage A author of a clean-room rewrite in the repository ~/2068-Leap-C (Leap-C, a C-language ROM
    for the Timex Sinclair 2068; Z80; sjasmplus). Your only deliverable is one new document,
    docs/TAPE_SIGNAL_SPEC.md: the specification from which a different author (Stage B), who will see nothing
    but your document, will write two new Z80 routines from scratch: TAPE_SEND_BLOCK (sends one cassette block)
    and TAPE_RECV_BLOCK (receives or verifies one). They replace routines that were ported from the stock
    Spectrum/TS2068 ROM (Amstrad copyright); the point of the exercise is that the new ones contain nothing
    derived from that ROM, and that we can show how they were written. So the rules on what you read matter
    as much as the document.

    ## What you may read

    1. Public descriptions of the cassette signal format: e.g. the TZX format documentation's description of
       "standard speed data" blocks (ID $10) and of pure tone / pulse sequence / pure data blocks (IDs $12-$14),
       general descriptions of the Spectrum/TS2068 tape signal (pulse widths in T-states, pilot lengths, sync
       pulses, two equal half-pulses per bit MSB first, the flag byte, the XOR checksum, header/data block
       structure). You may use the web (WebFetch/WebSearch) for this, but only for format descriptions: do NOT
       open any ROM disassembly or ROM listing (not skoolkid's / skoolkit's Spectrum ROM disassembly, not
       David Anderson's "Timex Sinclair 2068 ROM Disassembly", not any page quoting LD-BYTES/SA-BYTES/LD-EDGE
       code), and do not reproduce from memory any instruction sequence of those routines. Describe the
       SIGNAL and the required BEHAVIOUR, never the stock ROM's algorithm or its loop constants.
    2. Leap-C's own documents: spec.md (especially section 8 and section 2.2), project_plan.md, NOTICE,
       docs/milestones/M7.md, M9.md, M10.md, M11-beta.md, docs/EMULATORS.md, docs/HARDWARE_CHECKLIST.md.
    3. In platform/kernel/storage/storage.asm, ONLY these line ranges: 107-187 (constants and sentinels the
       callers use), 236-257 (STORAGE_SEND_BLOCK's contract header), 372-401 (STORAGE_RECEIVE_BLOCK's contract
       header, up to and including the label line), and 599-1062 (the callers: STORAGE_VERSION_WORD,
       STORAGE_SAVE, STORAGE_LOAD, STORAGE_REPORT_PROGRESS). Use `sed -n 'A,Bp'` with exactly those ranges.
       Do NOT read lines 1-106, 188-235, 258-371 or 402-598, do not grep that file without restricting the
       output to those ranges, and do not look at the file's git history (no git log -p / git show / git diff
       of it or of platform/deltas/kernel__storage__storage.asm.patch).
    4. The other callers and the environment: src/shell/tape.asm, src/rom/home.asm (TAPE_BLOCK and the
       COMP_TAPE section), src/rom/exrom.asm, src/runtime/library.asm (tape_save/tape_load's HOME part),
       platform/include/sysvars.inc and hardware.inc, platform/kernel/bank/bank.asm (paging; chunk 6),
       include/*.inc, budget.toml (the tape_block budget and the HOME reserve floor).
    5. The tests, which define the observable behaviour: tools/tapetest.py, tools/tapes.py, tools/lcharness.py
       (tape_insert, tape_capture), tools/memguard.py, tools/fusetest.py, tools/fusedrive.py, tools/hwkit.py,
       tools/exectest.py (its stack audit), tests/ cases about tapes.

    ## What you must NOT read

    The bodies of the old routines (the storage.asm ranges above), the stock ROM images (~/fuse-build/roms,
    anything named *.rom), any ROM disassembly, the frozen V2 repository ~/2068-Leap (and its archived storage
    code), anything under build/ that is a listing or disassembly (*.lst, *.sym are fine to skip entirely; you
    do not need them), spike/, docs/history/. If you open something and realise it contains the old code, stop
    reading it and say so in your final message.

    ## The document

    Write docs/TAPE_SIGNAL_SPEC.md, plain technical English, Markdown, matching the style of the repo's docs
    (spec.md). It must be complete enough that someone who has never seen this repository's tape code can write
    both routines and have them pass the tests. Cover at least:

    A. The signal (what TAPE_SEND_BLOCK must emit and TAPE_RECV_BLOCK must accept): the half-pulse model (each
       pulse = the MIC/EAR level held for N T-states, then toggled), the widths in T-states at the TS2068's
       3.528 MHz (pilot 2,168; sync 667 then 735; bit 0 = two half-pulses of 855, bit 1 = two of 1,710; bits
       MSB first), the pilot lengths (8,063 half-pulses before a header block, flag < $80; 3,223 before a data
       block, flag >= $80), the block = flag byte + payload + XOR checksum (of flag and payload), any closing
       pulse, and the tolerances the tests accept for SAVE's output (tools/tapetest.py widths_ok: -2..+16 T for
       contention; the pilot counts the decoder reports). Where the widths come from (public format) and how
       they relate to the stock Spectrum's 3.5 MHz.
    B. The hardware: port $FE (PORT_ULA): which bit is MIC out, which is EAR in, which bits are border, what
       reading the keyboard half-row containing SPACE looks like (port address high byte), PORT_FE_SHADOW and
       its role, what the port must hold on exit. Interrupts must be off while a block moves (and why: timing;
       Fuse's 32 T INT); who disables and who re-enables them. Paging: the routines live in HOME and run with
       chunk 6 paged to RAM, never touching the paging state; the stack is never in chunk 6 (bank rule 2);
       how much stack they may use (find out what the callers and the stack audits allow). NOBRK and BREAK
       rules as far as they concern these routines. The time cost of an instruction is the designer's problem,
       but state the TS2068 facts that matter (HOME ROM code runs uncontended; which RAM is contended; the
       -2..+16 T measured window).
    C. The two contracts exactly as callers depend on them: registers in (A = flag, IX, DE, carry for
       load/verify, and the Z-flag sentinel the callers set: STORAGE_NZ_SENTINEL; say what the new routine may
       do with it), registers out (carry; DE = bytes still outstanding on failure, = entry DE iff nothing was
       stored; what a successful send returns in carry and how SH_TAPE_SEND uses it), what is destroyed, the
       sysvars used (STORAGE_ENTRY_RETRY and its meaning), the exit state of port $FE / border. Every failure
       cause the receiver must report (timeout/no signal, SPACE, wrong flag, verify mismatch, dropout, checksum)
       and what each caller does with it (STORAGE_LOAD's retries and "touched" logic, the shell's TR_* reports,
       tape_load's results). Load vs verify. The leader search's bounded retry and the total give-up time the
       tests and spec.md state (about 2 minutes for a LOAD that finds nothing; how long a block search may
       wait in silence before the first edge).
    D. The receiver's required behaviour as observable requirements, not as an algorithm: what must count as a
       pilot, how long a pilot must be accepted from (the tests' synthesised tapes: tools/tapetest.py PILOT and
       the note in it; the stock data pilot is the shortest the suite uses), finding the sync, accepting either
       signal polarity, reading bits by measuring pulse widths, the flag check before storing, checksum, SPACE
       tested at every edge wait, a dropout (no edge for too long) ending the block as a failure, what happens
       with trailing pulses / the gap after the block. State the tolerance the receiver must have at least:
       real tapes and the emulators (ZEsarUX realtape sampled every 224 T; Fuse TZX direct recordings at 80 T
       a sample; WAV at 44.1 kHz) and a target envelope: every pulse width scaled by -25%..+25%, per-pulse
       jitter, one missing or one extra pilot pulse, a short dropout inside the pilot. Leave the choice of
       thresholds to the implementer but say what must be distinguished (sync vs pilot, 0 vs 1, timeout).
       The owner will append the measured envelope of the old receiver later; leave a section "Measured
       envelope of the beta.1 receiver" with a placeholder.
    E. Mutual readability: tapes from Leap-C's SAVE, from V2's ROM and from a stock TS2068/Spectrum must stay
       readable by each at the signal level (the content refusal is the header logic's business, unchanged).
    F. Constraints on the code: assembled in HOME with sjasmplus 1.23.1 (the repo's strict wrapper
       tools/sjasm_strict.sh; Leap-C's source style: see src/runtime/*.asm headers: `; ===` banner, In/Out/
       Destroys), size target <= 340 B for both together (the tape_block budget; the old pair measured 331 B),
       the HOME reserve floor. The test harness's needs: tools/lcharness.py tape_capture finds every `out
       (PORT_ULA), a` (bytes D3 FE) between the send routine's label and the receive routine's label and puts a
       ZEsarUX breakpoint on each (at most 5 slots, TAPE_SLOTS) to record the MIC level from bit 3 of A; say
       what the send routine's layout must respect so this works (or that the harness will be adapted:
       the new labels are TAPE_SEND_BLOCK and TAPE_RECV_BLOCK, send first). memguard's PC checks on the entry
       labels. The STORAGE_TEST_FAKE_SEND / STORAGE_TEST_FAKE_RECEIVE test hooks if they matter.
    G. A test list: which existing tests exercise each requirement (case names in tapetest.py, fusetest.py),
       so the Stage B author knows how to check the work.

    Be precise and cite where each fact came from (a public format description, a Leap-C file and line, a
    test). Where the callers rely on something the headers state but you cannot confirm from the allowed
    inputs, say so explicitly rather than guessing. Do not include any Z80 code taken from or modelled on the
    stock routines; short illustrative snippets of port I/O are fine if they are generic.

    When done, reply with: the document's path and size, a list of every file (and line range) and every web
    page you read, and any point where you were unsure whether something was allowed. Do not commit.

Addendum sent to Stage A while it worked (the orchestrator's description of Fuse's loader detection; abridged where marked ...):

    Addendum from the orchestrator (an extra requirement for section D/F; do not go and read Fuse's loader.c
    yourself -- its acceleration part pattern-matches the stock ROM's code, so it is off-limits; here is the
    only part that matters, described):

    Fuse 1.9.1 (default settings detect_loader=1) starts and stops its tape deck by watching reads of the ULA
    port ($FE, any read whose port address has A0=0, keyboard reads included). For each such read it computes
    dt = T-states since the previous such read and db = (B register now) - (B at the previous read), mod 256.
     - Tape stopped: a read with dt <= 500 and db = +1 or -1 increments a counter, any other read resets it;
       at 10 successive such reads Fuse presses PLAY.
     - Tape playing: a read with dt > 1000, or db not in {0, +1, -1}, increments a counter, a good read
       resets it; at 2 successive bad reads Fuse presses STOP.
    Leap-C's Fuse suites never press play themselves: they rely on this. So the receiver's port reads ... must
    satisfy it ... Please put this in the specification as a hard requirement with this source. Also state
    that Fuse's separate "accelerate_loader" (default on) may or may not recognise the new code and that
    correctness must not depend on it either way.

After Stage A finished, the orchestrator replaced the specification's §10 placeholder with the beta.1
receiver's measured envelope (black-box, `tools/tapetol.py`).

### 5.2 Stage B, the tape routines

    You are the Stage B author of a clean-room rewrite in the repository ~/2068-Leap-C (Leap-C, a C-language ROM
    set for the Timex Sinclair 2068; Z80; sjasmplus 1.23.1 through tools/sjasm_strict.sh). You write two new
    Z80 routines from a specification alone: TAPE_SEND_BLOCK (sends one cassette block) and TAPE_RECV_BLOCK
    (receives or verifies one), in the new file src/runtime/tapeblock.asm (now a 6-line placeholder), which
    src/rom/home.asm assembles into the HOME ROM between COMP_TAPE_BEGIN and COMP_TAPE_END. They replace
    routines that were ported from the stock Spectrum/TS2068 ROM (Amstrad copyright). The point is that the new
    code contains nothing derived from that ROM and that we can show it, so the reading rules below matter as
    much as the code.

    ## Your input

    docs/TAPE_SIGNAL_SPEC.md is your specification: the signal, the hardware, the two contracts (§4), the
    receiver's required behaviour (§5), the tolerance (§6, and §10: the old receiver's measured envelope, which
    yours must at least match), the constraints (§8) and the tests (§9). Read all of it first. Design the
    receiver yourself (how you find the pilot, sync, how you time edges, thresholds); the spec deliberately
    leaves that to you.

    ## What you may read

    - docs/TAPE_SIGNAL_SPEC.md; spec.md; docs/ except docs/history/.
    - Leap-C source for integration and style: src/ (all of it), include/, platform/include/ (sysvars.inc,
      hardware.inc), platform/kernel/bank/bank.asm, budget.toml, Makefile.
    - The tests and tools: tools/ (tapetest.py, tapes.py, tapetol.py, lcharness.py, memguard.py, fusetest.py,
      fusedrive.py, exectest.py, run_tests.py, ...), tests/.
    - Build outputs of YOUR code (build/*.lst, *.sym after you build).

    ## What you must NOT read

    - platform/kernel/storage/storage.asm (any part, now or in git history), platform/deltas/ (any patch or
      .cut file), and the git history of any file under platform/ (no git log -p / git show / git diff /
      git blame of them, no checkout of older commits, no `git stash` tricks). Do not look at commits before
      the current HEAD for any tape-related file.
    - Any stock ROM image (~/fuse-build/roms, anything *.rom), any disassembly of one, and do not disassemble
      or dump the beta.1 Leap-C images (/tmp/claude-1000/-home-charlie-day-2068-Leap-C/8c77c544-c043-4651-89b0-650615b8230f/scratchpad/beta1/*.bin): you may only RUN them through
      tools/tapetol.py for the envelope comparison.
    - ROM disassemblies or listings anywhere (skoolkid/skoolkit's Spectrum ROM disassembly, David Anderson's
      TS2068 disassembly, any web page or book listing LD-BYTES / SA-BYTES / LD-EDGE code), Fuse's loader.c
      (its acceleration code pattern-matches the stock routines; the spec §5.8 already describes the part you
      need), the frozen V2 repository ~/2068-Leap, ~/ts2068-debug's sources beyond what the harness needs,
      spike/, docs/history/, and build/release or build/kit (old images). Do not search the web.
    - Do not write from memory any instruction sequence you know from the stock ROM's tape routines. If you
      notice that your design is converging on a sequence you recognise from it, choose a different
      structure and say so in your report.
    If you open something and realise it contains old tape code, stop reading it and say so in your report.

    ## Constraints (summary; the spec rules)

    R1-R13 of the spec. In particular: size <= 331 B for both routines together (340 B allowed; say if you need
    it), at most 34 B of stack, interrupts disabled at entry, port $FE MIC on bit 3 written only by
    `out (PORT_ULA), a` (at most 5 such instructions, all between TAPE_SEND_BLOCK and TAPE_RECV_BLOCK, the send
    routine first in the file), Fuse's loader detection (§5.8), every contract of §4 (carry, DE outstanding,
    IX walking, load/verify, SPACE handling, STORAGE_ENTRY_RETRY), the pulse widths within -2..+16 T of
    nominal on ZEsarUX. Use Leap-C's source style (src/runtime/*.asm: the `; ===` banners, In / Out /
    Destroys headers, comments in your own words). Explain the timing of every pulse in comments (T-state
    counts of the loops) so a reviewer can check it. Put a file header that says the file is Leap-C's own
    clean-room code written from docs/TAPE_SIGNAL_SPEC.md.

    ## Building and testing

    - `make prod` (production images in build/), `make build` (also the test images and the libraries).
    - The cassette suite: `python3 tools/tapetest.py --port 10770` (all cases, roughly 20-40 minutes; it starts
      its own ZEsarUX on that port), or a subset by name substring, e.g. `python3 tools/tapetest.py --port
      10770 roundtrip`. Read its docstring and the case list first. `python3 tools/run_tests.py --help` for the
      pool (`--suites tape` style options, if present).
    - Fuse: `python3 tools/fusetest.py save wav lib` and `python3 tools/fusetest.py corpus --only <substr>`
      (the full corpus is 780 cases; run at least a slice, e.g. --only tests/c/).
    - The envelope: `python3 tools/tapetol.py --build /tmp/claude-1000/-home-charlie-day-2068-Leap-C/8c77c544-c043-4651-89b0-650615b8230f/scratchpad/beta1 --build build` compares the beta.1
      receiver with yours; it must print no NARROWER line (yours must accept every case the old accepts).
    - The kit: `python3 tools/hwkit.py --help` (its WAV verification on both emulators).
    - Use free ports 10770-10790 for your emulators; other sessions may use 10760-10769 and 10850+.
    - If a test seems to require something the spec does not say, report it rather than weakening the test;
      do not modify any test or tool, except that you may add scratch scripts in
      /tmp/claude-1000/-home-charlie-day-2068-Leap-C/8c77c544-c043-4651-89b0-650615b8230f/scratchpad/tapeb/. Edit only src/runtime/tapeblock.asm (and, if strictly needed for
      integration, tell me what else and why instead of doing it).

    ## Report

    Reply with: the final size of each routine (bytes), its stack use, a short description of your receiver's
    design (how it finds the pilot and sync, how it decides 0/1, timeouts), the measured SAVE pulse widths
    (tapetest roundtrip's extra data), the results of every test you ran (pass/fail counts, failures), the
    tapetol comparison table, anything in the spec you found wrong or unclear, and the complete list of files
    you read (and any web page). Do not commit.

Messages sent to the Stage B author while it worked (abridged; nothing was added that is not in the originals):

1. "You may use the shrink-z80 skill for the size pass, at ~/z80-skills/skills/shrink-z80/ (SKILL.md, then
   references/hard-contract.md, dispatcher.md, asm-micro.md and z80-byte-evidence.md; its scripts by absolute
   path on src/runtime/tapeblock.asm only). I checked it: it contains no stock-ROM tape code, so the reading
   rules still hold. Every byte-saving change must keep the cycle-counted pulse timing (or re-tune it) and then
   re-pass the tests that check timing. Report each shrink applied, the bytes saved and how it was verified.
   Aim for 331 B or less."
2. "The tapetest cross-version failure (KeyError: 'TAPE_SEND_BLOCK') came from my harness rename, not from your
   code: V2's reference ROM has no TAPE_SEND_BLOCK label. tools/lcharness.py now falls back to V2's own names.
   Rerun cross-version. Do not change tools yourself."
3. "One behaviour is missing, and it is user-visible on real hardware: the border stripes ... Neither of your
   routines writes the border now. Please add the stripes: the sender toggles a border colour bit together with
   MIC on every edge; the receiver changes the border at every edge it sees, keeping port $FE's MIC bit as it
   was; on exit both restore the border from PORT_FE_SHADOW. Keep every timing, Fuse's loader detection and the
   size limit; re-run the timing tests."

4. "One more change, found by the independent-decoder check: read the amendment at the end of
   docs/TAPE_SIGNAL_SPEC.md §2.4. After the checksum's last bit the sender must toggle MIC once more about 855 T
   later (one closing 0-width half-pulse), then return. A Fuse recording of SAVE converted with tape2wav and
   decoded by fuse-utils' audio2tape gives only the header block; the same with beta.1's SAVE gives both. Add it
   in the sender's normal exit; keep the border restore and the capture-slot rules; re-run the tests."
   (The author added it, and merged the receiver's search and sync-wait loops to stay within the 318 B budget
   then recorded; the lock became 255 pilot half-pulses in a row.)

### 5.3 Stage B, the glyph

    You are a clean-room author for one small Z80 routine in the repository ~/2068-Leap-C (Leap-C, a ROM for the
    Timex Sinclair 2068; assembler sjasmplus 1.23.1 through tools/sjasm_strict.sh; `make prod` builds the
    production images in build/). The code you write replaces code that matched the stock Spectrum ROM, so you
    must write it from the description below alone.

    ## Rules on what you may read

    Do NOT read: the git history of platform/kernel/graphics/graphics.asm or of platform/deltas/ (no git log -p,
    git show, git diff, git blame of them), platform/deltas/kernel__graphics__graphics.asm.patch, any stock ROM
    image (~/fuse-build/roms, *.rom), any ROM disassembly (skoolkid/skoolkit, Anderson's TS2068 disassembly, any
    web page about the Spectrum ROM's PO-GR-1/PO-GR-2/block-graphics code), the frozen V2 repository ~/2068-Leap,
    and anything under spike/ or docs/history/. Do not search the web. You may read the rest of graphics.asm
    (other routines, for the style), platform/include/sysvars.inc, the tests, and the build outputs that you
    produce yourself after your change.

    ## The task

    In platform/kernel/graphics/graphics.asm, the routine GFX_CHAR_TO_FONT_OFFSET has a local label
    `.is_block_graphics:` followed by a placeholder (`; LEAP-C DELTA D21 ...`, `scf`, `ret`). Replace the
    placeholder (keep the label and the D21 comment line) with your implementation.

    Contract at the label (reached by `jr c, .is_block_graphics` from the routine's dispatch):
    - A = E = the character code, 128..143 (block graphics). D holds the caller's value and must not change.
    - Out: carry clear, HL = BLOCK_GFX_SCRATCH (an 8-byte RAM buffer, sysvars.inc) holding the glyph that was
      just generated: 8 bytes, top pixel row first, bit 7 of each byte the leftmost pixel.
    - Destroys: AF, BC, E, HL (nothing else; no other memory than the 8 bytes; the stack may be used).
    - The glyph: let n = code - 128 (0..15). The 8x8 cell is split into four 4x4 quarters. Bit 0 of n set =
      the top-right quarter is ink (all 16 pixels set), bit 1 = top-left, bit 2 = bottom-right, bit 3 =
      bottom-left. So rows 0-3 are (bit1 ? $F0 : 0) | (bit0 ? $0F : 0), rows 4-7 are (bit3 ? $F0 : 0) |
      (bit2 ? $0F : 0). Examples: 128 = blank, 143 = all ink, 129 = rows 0-3 $0F and rows 4-7 $00, 138 (n=10:
      bits 1 and 3) = all rows $F0.

    Write it as you would naturally, small (the old one was 53 lines of source including comments; aim for
    fewer bytes if you can, but clarity first), in the file's style (comments after `;`, aligned like the code
    around it). Comment what it does in your own words.

    ## Checks

    1. `make prod` succeeds (strict assembly).
    2. Verify the 16 glyphs by simulating or by running: the simplest is a small Python Z80 check you write
       yourself (a tiny interpreter for the few instructions you use is fine), or run the corpus case
       tests/lib/text/block_graphics.c on ZEsarUX: `python3 tools/exectest.py --help` / tools/run_tests.py
       explain how; a single case can be run with `Machine(build, port).start()` then
       `exectest.check_case(m, path)` from tools/ (see tools/lcharness.py, tools/exectest.py; use a free port
       such as 10851). Report the glyph bytes you verified for all 16 codes.
    3. Report the size in bytes of your code (from build/leapc_home.lst or the symbol addresses of
       .is_block_graphics and .is_udg in build/leapc_home.sym, after your build).

    Do not commit. Reply with: the code you wrote (verbatim), its size, how you verified it (and the results),
    and the list of files you read.
