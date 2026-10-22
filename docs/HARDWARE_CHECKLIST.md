# Leap-C: physical TS2068 hardware checklist

**Status: NOT TESTED ON PHYSICAL HARDWARE. Owner-accepted qualification deviation (2026-10-21).** No Timex Sinclair 2068 was available for Phase 9. The owner accepted recording the physical checks as a qualification deviation, not as passes. Everything below was established on two emulators instead:

- **ZEsarUX 13.0**, the qualification emulator, which runs every suite;
- **Fuse 1.9.1**, an independent emulator, which emulates the TS2068's own 60 Hz frame (`tools/fusetest.py`, `tools/timingcmp.py`).

The items are the tests to run when a machine is available. For each result, record the date, the machine and its board revision, the observer, and the SHA-256 of both images (`build/kit/CHECKSUMS.txt`).

An emulator is not the hardware. These can differ on a real machine:

- the keyboard's switches (bounce, ghosting);
- the cassette's levels, wow and flutter;
- the display's memory contention;
- the SCLD's paging of the EXROM into chunk 6;
- the AY;
- the RAM's contents at power-on;
- the EPROMs' timing.

Each item gives what the emulators show. A difference on the hardware is a finding. Record it with the steps and the screen.

## 0. The kit

`make kit` builds `build/kit/` from the production images (`tools/hwkit.py`). `tools/hwkit.py --verify` loads every check program's WAV in both emulators and records what they show in `docs/hardware/EMULATOR_RESULTS.md`, with the images' SHA-256s; the kit carries a copy when it is for the same images.

| File | What it is |
|---|---|
| `eprom/leapc_home_27128.bin` (`.hex`) | the HOME ROM, 16,384 B, for a 27128 (or 27C128): the 16K system ROM, `$0000-$3FFF` |
| `eprom/leapc_exrom_2764.bin` (`.hex`) | the EXROM, 8,192 B, for a 2764 (or 27C64): the 8K extension ROM, paged into chunk 6 (`$C000-$DFFF`) |
| `tapes/hN_*.tap`, `.tzx`, `.wav` | the hardware check programs H1-H10 (`docs/hardware/*.c`) |
| `tapes/exNN.tap`, `.tzx`, `.wav` | the examples of `docs/EXAMPLES.md` (also in `tests/doc/`) |
| `CHECKSUMS.txt` | every file: size, SHA-256, CRC-32 and the byte sum (32 and 16 bits; programmers show one of these) |
| `EMULATOR_RESULTS.md` | each check program's screen on ZEsarUX and Fuse |

**EPROMs.** Program the HOME image into a 27128 and the EXROM image into a 2764, and compare the programmer's checksum with `CHECKSUMS.txt`. The TS2068's own ROMs are mask ROMs. Depending on the board, an EPROM in their sockets may need an adapter or a ROM-replacement board, because the pinouts differ in places. Check the board before fitting anything. There is no DOCK-cartridge build: the images replace the internal ROMs. (`build/leapc_exrom.dck` is for emulators only.)

**Tapes.** The WAVs are 8-bit mono PCM at 44.1 kHz, with the stock ROM's pulses at the TS2068's 3.528 MHz clock: what Leap-C's own SAVE sends. Play them from a computer or phone into the EAR socket, or record them onto a cassette first. Start at full volume with the tone controls flat. `fuse-utils`' `audio2tape`, an independent decoder, reads every kit WAV back to exactly its tape's blocks. The `.tap` and `.tzx` files are the same tapes for tape players and emulators.

## 1. Power-on and boot

| # | Step | Expected (both emulators) | Result |
|---|---|---|---|
| 1.1 | Power on. Repeat after the machine has been off for a minute, so the RAM holds other contents | the editor: an empty screen, the status bar `LINE 1/0` on row 23 with the red, green and blue swatch, the cursor at the top left; the start-up chime | NOT TESTED (owner-accepted deviation) |
| 1.2 | `LOAD ""` with H1 (`tapes/h1_hello.wav`), `RUN` | the four lines of H1; `EXIT 0` | NOT TESTED (owner-accepted deviation) |
| 1.3 | Look at H1's second and third lines on the TV or monitor | the digit `1` (a flag and a base), the letter `l` (a tail), `I`, `\|`, `0` (slashed) and `O` all distinct (platform delta D13) | NOT TESTED (owner-accepted deviation) |
| 1.4 | Reset during a program (a reset button if fitted, or a power cycle) | a cold start: the editor as in 1.1, the source cleared | NOT TESTED (owner-accepted deviation) |

Emulator evidence: the cold start reaches the editor's key wait in 4,048,989 T on Fuse and 4,626,111 T on ZEsarUX (the difference is the boot's frame waits at 60 and 50 Hz). From eight power-on RAM patterns (random, `$FF`, `$55AA`, address-low-byte, and the reset button after a session), the boot is identical to a boot from zeroed RAM, to the byte and the T-state (`tools/poweron.py`, in `make test`).

## 2. Keyboard

| # | Step | Expected | Result |
|---|---|---|---|
| 2.1 | Type the letters, CAPS SHIFT + letters, the digits | as typed, on the edit line | NOT TESTED (owner-accepted deviation) |
| 2.2 | SYMBOL SHIFT + each key of the C map (`spec.md` §6.2): `[` Y, `]` U, `{` F, `}` G, `\|` S, `~` A, `^` H, `\` D, and the stock ones (`"` P, `;` O, `:` Z, `<` R, `>` T, `=` L, `+` K, `-` J, `*` B, `/` V, `?` C, `,` N, `.` M, `!` 1, `@` 2, `#` 3, `$` 4, `%` 5, `&` 6, `'` 7, `(` 8, `)` 9, `_` 0) | each character as typed; H2 (`keys`) shows each key's character and code | NOT TESTED (owner-accepted deviation) |
| 2.3 | CAPS SHIFT + 5, 8, 7, 6 (cursor), + 0 (delete), + 1 (delete line), + ENTER (insert line) | the editor moves and edits as in the emulators | NOT TESTED (owner-accepted deviation) |
| 2.4 | Press two letter keys at the same moment | nothing typed | NOT TESTED (owner-accepted deviation) |
| 2.5 | Hold a letter key | it repeats after about 0.6 s (35 frames), then every 5 frames | NOT TESTED (owner-accepted deviation) |
| 2.6 | Type a 100-character line quickly | every character, no dropped keys (V1 hardware dropped quick taps) | NOT TESTED (owner-accepted deviation) |
| 2.7 | Type `int x;` and ENTER | `int` shown bold | NOT TESTED (owner-accepted deviation) |

Emulator evidence: all 95 printable characters typed on the keyboard matrix of both emulators; the editing keys on ZEsarUX's matrix act as their codes do (shell case `keys-editing-matrix`); 31 programs typed and run on Fuse's matrix.

## 3. Programs and the workflow

| # | Step | Expected | Result |
|---|---|---|---|
| 3.1 | Type `docs/EXAMPLES.md`'s first program, `RUN` | its output; `EXIT 0` and `IMAGE n B  HEAP n B` | NOT TESTED (owner-accepted deviation) |
| 3.2 | Type `float third = l.0 / 3;` (a letter `l`) in a `main`, `RUN` | `ERROR 23: UNDECLARED IDENTIFIER`, `LINE 3  'l'`, the cursor on that line | NOT TESTED (owner-accepted deviation) |
| 3.3 | `beep(1, 99);` in a `main`, `RUN` | `RUNTIME ERROR 4: BAD ARGUMENT` | NOT TESTED (owner-accepted deviation) |
| 3.4 | `RUN` a short program and keep ENTER held for a second | the report stays until ENTER is released and another key pressed (Phase 9 fix) | NOT TESTED (owner-accepted deviation) |
| 3.5 | `LOAD ""` each example tape (`ex01` ... `ex26`), `RUN` | as `docs/EXAMPLES.md` shows | NOT TESTED (owner-accepted deviation) |
| 3.6 | H6 (`float`), `RUN` | `SQRT 2 = 1.414213`, `SQRT 10 = 3.162277`, `1/3 = 0.333333333`, `FLOAT PASS`: every operation pages the EXROM in and out | NOT TESTED (owner-accepted deviation) |

## 4. BREAK

| # | Step | Expected | Result |
|---|---|---|---|
| 4.1 | H8 (`brk`), `RUN`, then CAPS SHIFT + SPACE | `BREAK`, `LINE 2`; held longer, the report stays until released | NOT TESTED (owner-accepted deviation) |
| 4.2 | BREAK during `pause(30000);`, during a float loop, during `beep(600, 0);` | `BREAK` at once; the note stops | NOT TESTED (owner-accepted deviation) |
| 4.3 | BREAK (or SPACE) during `SAVE`, `LOAD`, `tape_save`, `tape_load` | `BREAK`; nothing changed | NOT TESTED (owner-accepted deviation) |

## 5. Timing at 60 Hz

| # | Step | Expected | Result |
|---|---|---|---|
| 5.1 | H3 (`hz60`), `RUN`, a stopwatch from the first beep to the second | `600 FRAMES`; **10.0 s** (12.0 s would mean a 50 Hz frame) | NOT TESTED (owner-accepted deviation) |
| 5.2 | H7 (`sound`), `RUN`, with a tuner | eight notes from middle C, 0.5 s each; then A at 440 Hz for 2.0 s | NOT TESTED (owner-accepted deviation) |
| 5.3 | Listen to the start-up chime | C, E, G (V2's chime; ZEsarUX plays it at 50 Hz, so a TS2068 takes five sixths of that time) | NOT TESTED (owner-accepted deviation) |

A frame is 1/60 s on a TS2068: `frames()`, `pause(n)`, `beep(frames, ...)` and the keyboard's repeat count them. Fuse emulates that frame (224 T × 262 lines = 58,688 T). ZEsarUX 13.0 runs its TS2068 with the 48K Spectrum's 50 Hz frame (69,888 T), so a program there sees 50 frames a second.

## 6. Display contention

| # | Step | Expected | Result |
|---|---|---|---|
| 6.1 | H4 (`cont1`), `RUN`: a loop whose code is in image region 1 (chunk 6) | `REGION 1: n FRAMES`: Fuse **313**, ZEsarUX 262 (at 50 Hz) | NOT TESTED (owner-accepted deviation) |
| 6.2 | H5 (`cont4`), `RUN`: the same loop with its code in region 4 (`$6000-$77FF`, contended) | `REGION 4: n FRAMES`: Fuse **385**, ZEsarUX 301; record the hardware's ratio to 6.1 (Fuse 1.230, ZEsarUX 1.149) | NOT TESTED (owner-accepted deviation) |

Emulator evidence (`tools/timingcmp.py`, `build/timing.md`): code in region 4 runs 23% slower than in region 1 on Fuse's TS2068 model and 15% slower on ZEsarUX's 48K model. Uncontended code differs by 0.6% between the two (the ISR runs 60 times a second on Fuse, 50 on ZEsarUX). The real machine decides which model holds.

## 7. Tape (a real cassette recorder)

| # | Step | Expected | Result |
|---|---|---|---|
| 7.1 | A 20-line program: `SAVE "t"`, `NEW`, `LOAD "t"`, then `VERIFY "t"` | `SAVED t`, `LOADED t` with the same program, `VERIFIED t` | NOT TESTED (owner-accepted deviation) |
| 7.2 | `LOAD ""` of each kit WAV played into EAR | `LOADED name`; at what volume it loads reliably | NOT TESTED (owner-accepted deviation) |
| 7.3 | H9 (`tapedata`): record, ENTER, rewind, play, ENTER | `LOADED 2000 BYTES, 0 WRONG`, `TAPE PASS` | NOT TESTED (owner-accepted deviation) |
| 7.4 | `LOAD ""` of a Leap V2 or stock TS2068 BASIC tape | `BAD TAPE VERSION`, the program as it was | NOT TESTED (owner-accepted deviation) |
| 7.5 | Stop the tape in the middle of a LOAD | `LOAD FAILED` after the search gives up (about 2 minutes), or BREAK at once; no crash | NOT TESTED (owner-accepted deviation) |

Emulator evidence: the cassette suite (21 cases, real tape signals in ZEsarUX); on Fuse a SAVE recorded by its tape deck loads back; H9 runs on Fuse with `tape_save` recorded and `tape_load` played back; 745 corpus programs LOADed from tape on Fuse by the ROM's own loader.

## 8. Soak

| # | Step | Expected | Result |
|---|---|---|---|
| 8.1 | H10 (`soak`), `RUN`, leave it at least an hour, then press a key | `n ROUNDS, SOAK PASS 0`; record n and the frames shown | NOT TESTED (owner-accepted deviation) |
| 8.2 | Leave the editor idle for an hour, then type | responsive, the source intact | NOT TESTED (owner-accepted deviation) |

Emulator evidence: H10 for 30 emulated minutes on each emulator: both pass with no failed check. ZEsarUX ran 15,694 rounds in 92,434 frames (30.8 minutes at its 50 Hz); Fuse ran 15,247 rounds in 108,005 frames (30.0 minutes at 60 Hz). The program prints the frame count modulo 65,536: 26,898 and 42,469.

## 9. What to watch for on the hardware

- **EXROM paging (chunk 6).** Programs run with chunk 6 as RAM. Every float operation, `beep` and the tape functions page the EXROM in and out (H6, H10). The banking invariants are checked on every program in ZEsarUX only.
- **Contention.** The two emulators' models differ (§6), and neither is the hardware.
- **The keyboard.** Debounce with real switches; ghosting with three keys; BREAK's reliability.
- **The cassette.** Levels and the loader's margins: the ROM's pulses are timed at 3.528 MHz.
- **Power-on RAM.** Eight emulated patterns, not a real DRAM's.
- **The EPROMs.** Access time, adapters, and the programmer's checksum against `CHECKSUMS.txt`.

Record failures with the steps, the screen and, if possible, a reproduction in ZEsarUX (`tools/lcharness.py`) or Fuse (`tools/fusedrive.py`).
