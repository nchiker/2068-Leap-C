# The Leap-C runtime cartridge (release 1.2.0; new in 1.1.0)

A **runtime cartridge** runs one compiled Leap-C program on a **stock Timex Sinclair 2068**: the stock HOME ROM and EXROM stay installed, and the program starts from the DOCK socket. There is no editor, no compiler, no shell and no source on the cartridge. After the program ends it shows the one-row report (`EXIT n`, `RUNTIME ERROR n MESSAGE` or `BREAK`) and a key runs the program again from a cold start.

The program is compiled by the **release** Leap-C ROM (1.2.0's images; a program compiled by 1.0.0 or 1.1.0 needs their own cartridge build, see the identity below), and the cartridge's HOME keeps every release routine at its release address, so the compiled code runs unchanged. The cartridge is **qualified on emulators only** (Fuse 1.9.1 and ZEsarUX 13.0); it has not been run on a physical TS2068 or in a physical cartridge.

## The files

In `leapc-1.2.0-cartridge.zip`:

| File | What it is |
|---|---|
| `demo/hello.dck` | the demo program as a Timex Dock cartridge, for the emulators |
| `demo/hello.bin` | the same as a flat 64 KB image, for a physical cartridge (e.g. a PicoROM) |
| `roms/leapc_cart_home.bin` | the cartridge's HOME, 16 KB (DOCK chunks 0-1) |
| `roms/leapc_exrom.bin` | the release EXROM, 8 KB (DOCK chunk 6), byte-identical to the release's |
| `tools/cartpack.py`, `tools/cart_build.py` | the packer (the reference for ports to other languages) and the CRC it imports |
| `SHA256SUMS` | every file's SHA-256 |

## Running a cartridge

Always on the machine's **stock** ROMs: the stock ROM finds the cartridge's header in the DOCK and hands over to it. Do not load Leap-C's own ROM images.

- **Fuse** (qualified on 1.9.1): `fuse --machine ts2068 hello.dck`, with Fuse's own TS2068 ROMs (`tc2068-0.rom`, `tc2068-1.rom`). Fuse takes the `.dck` as a file to insert (this is how tools/fusedrive.py starts it, and how it was tested); from the GUI, the Media menu's Timex Dock cartridge insert should do the same (not tested). Start with `--no-auto-load` if your settings load tapes on their own.
- **ZEsarUX** (qualified on 13.0): start the TS2068 (`--machine ts2068`) with its stock `ts2068.rom`, then `smartload hello.dck` (the File menu's Smart load, or ZRCP's `smartload`). It runs the cartridge at once.
- **TSRun**: not tested with Leap-C's cartridge. The Leap IDE's notes say TSRun inserts a dock cartridge (`insertDock`) with its stock ROMs, but no Leap-C cartridge has been run there.
- **A physical cartridge** (a PicoROM or an EPROM board): burn or load the flat `hello.bin`. The eight 8 KB chunks are in address order (chunk n at offset n x 8192); the cartridge uses chunks 0, 1, 4, 5 and 6 (and 2 for a program over 16 KB), and `$FF` fills the others. **Untested.**

What you should see: the screen clears and the program runs. For the demo, `Hello from a cartridge!`, `Sum of squares 1..10 = 385` and a diagonal line; then `EXIT 0` on the bottom row. Press a key and it runs again.

## Making a cartridge

In this repository, with ZEsarUX 13.0 and the EXROM patch set up as for `make test` (CONTRIBUTING.md):

    make cart PROG=myprogram.c              # build/cart/myprogram.dck and myprogram.bin
    make cart PROG=myprogram.c LIB=shapes   # a program that uses a loaded library (build/libs/shapes.bin)
    make cart-demo                          # build/cart/hello.dck and hello.bin from examples/cart_hello.c

`make cart` first builds the cartridge's HOME (`build/cart/leapc_cart_home.bin`, `-DLEAPC_CART`), checks it against the release (`tools/cart_check.py`) and runs the packer's self-test; none of that needs an emulator. With `PROG=` it runs `tools/c2cart.py`, which compiles the program **on the release ROM** in ZEsarUX the way the shell's `RUN` does (stopping before the program runs), reads the compiled program back out of the machine (per image region its code and its static data; a loaded library's region 3; region 4 when `#pragma hires` reserved it), and packs it. The program must compile without errors and must fit the regions. `c2cart.py --image x.img` writes the program image alone.

A program that needs the keyboard, the clock or the tape works as it does under `RUN`, subject to the differences below.

## The memory map

| DOCK chunk | Address | Content | Mapped (port `$F4`, the HSR) |
|---|---|---|---|
| 0-1 | `$0000-$3FFF` | the cartridge HOME | always (`$03`, or `$43`) |
| 2 | `$4000-$5FFF` | the program image's continuation (images over 16 KB) | only in the copy, interrupts off |
| 3 | `$6000-$7FFF` | absent | never (RAM: image region 4, display file 2) |
| 4-5 | `$8000-$BFFF` | the program image | only in the copy, interrupts off |
| 6 | `$C000-$DFFF` | the release EXROM | while `BANK_EXROM_DEPTH` > 0 (`$43`); otherwise RAM (image region 1) |
| 7 | `$E000-$FFFF` | absent | never |

Port `$FF` bit 7 stays 0 (DOCK) from the cold start on; the stock ROMs are never selected again. `$F4` is written only with `$03`, `$33`, `$37` and `$43`. Cartridge-specific code is in HOME's free space: 252 bytes at `$3D60-$3E5C` in 1.2 (372 bytes of the space are left; 1.1: `$3DEF-$3EEB`, 229). The release's labels keep their addresses. The LROS header, which the stock ROM reads (`$00`, `$01`, the entry address, chunk byte `$BC`), takes `$0000-$0004`; in 1.1 that moved `IO_KEY_SCAN_ROW` from `$0004` to `$000D`, and since 1.2 (platform delta D27) neither build has that routine, so no label moves. A program that `PEEK`s `$0000-$0007` therefore reads the header.

At the hand-off the stock ROM jumps to `CART_ENTRY` with interrupts on, IM 1, SP `$61FE`, `$F4` = `$43`, `$FF` = `$00`. `CART_ENTRY` disables interrupts, sets its own stack, quiets the AY and runs the release cold start, which ends in the cartridge's loader instead of the shell.

## The program image

The image sits at DOCK `$8000` (chunks 4-5); a longer one continues at DOCK `$4000` (chunk 2). Words are little-endian except the final CRC.

| Offset | Size | Content |
|---|---|---|
| 0 | 4 | `"LCPG"` |
| 4 | 1 | format, `1` |
| 5 | 2 | identity (below) |
| 7 | 2 | `RUN_MAIN`, the address of `main` |
| 9 | 1 | `RUN_VOID`, 1 if `main` is `void` |
| 10 | 16 | `IMG_LIM`: for the four regions, [low][high] words (the compiler's limits; `mode(1)` reads region 4's) |
| 26 | 1 | `LIB_LOADED`: `$F4` if a library is carried in region 3, else 0 |
| 27 | n | blocks `[length:2][address:2][bytes]`, length 1 to 8192, inside one region; ended by a length of 0 (`00 00`) |
| end | 2 | CRC-16/CCITT-FALSE of every byte before it, **high byte first** (so the CRC over the whole image is 0) |

The header is 27 bytes. The blocks are, per region, its code `[base, low)` and its static data `[high, end)`, a library's whole region 3 (`$F400-$F7FF`), and region 4 (`$6000-$77FF`) up to its last non-zero byte for `#pragma hires`. The regions: 1 `$C000-$DFFF`, 2 `$E000-$F17F`, 3 `$F400-$F7FF`, 4 `$6000-$77FF` (the compiler's order in `IMG_LIM`). The cartridge refuses (shows `NO PROGRAM`) an image with a wrong signature, format or identity, a block over 8 KB, or a wrong CRC; `cartpack.verify()` makes the same checks.

### The containers

- **`.dck`**: one DOCK bank, as 2068-Forth writes it: a byte 0 (bank id), eight descriptor bytes (chunks 0-7: 2 = 8 KB of ROM follows, 0 = absent), then the present chunks' 8 KB each, in chunk order: 0, 1, 2 (only for an image over 16 KB), 4, 5, 6. So hello.dck is 9 + 5 x 8192 bytes.
- **Flat `.bin`**: 65,536 bytes, the eight chunks in order, `$FF` in absent chunks. Unused bytes of chunks 4, 5 and 2 are `$FF`.

## The identity

A program's addresses are valid only against the ROM that compiled it. The identity is the **CRC-16/CCITT-FALSE** (polynomial `$1021`, initial value `$FFFF`, no reflection, no final xor, most significant bit first) of the release HOME image (`leapc_home.bin`, 16,384 bytes) followed by the release EXROM image (`leapc_exrom.bin`, 8,192 bytes). For Leap-C 1.2.0 it is **`$F6E9`** (1.0.0 and 1.1.0, which share their images: `$E90E`). The cartridge holds it as a constant (0 bytes of either ROM image carry it) and refuses any image with another. `python3 tools/cart_build.py --identity` prints it in the repository.

## How it differs from RUN

The reports and the final screen (rows 0-22, text, bitmap and attributes) match `RUN` on the release ROM for the 115 programs compared. Expected differences:

- `malloc` returns other addresses: there is no source, so the heap starts at an empty source store's end (for one program `$7802` against `$7868`).
- `PEEK` of `$0000-$0007` reads the cartridge's header, not the release's code.
- UDGs are blank at every start (the cold start clears them; under the shell they persist between runs).
- The cartridge reports no line number (`RUN_FNLINES` is 0, the report never looks for a source line) and has no editor to return to; a key restarts the program from a cold start, re-copying the image, so the program's static data is fresh each run.
- `tape_save` and `tape_load` are in the release EXROM the cartridge carries, but they have **not been tested from a cartridge**. The shell's `SAVE`, `LOAD` and `LIB` commands do not exist (a library travels inside the image).

## Limits

- The image is at most 24 KB: 16 KB in chunks 4-5 plus 8 KB of chunk 2. The regions hold about 19.9 KB, so every program the compiler accepts fits. The regions' own limits are the compiler's (Appendix E of the manual); a program too big for them does not compile.
- One program per cartridge, one library at most (region 3).
- The image is checked and copied only at the cold start; there is no way to select among programs.

## A known hazard

An interrupt exactly between the stock ROM's jump to `CART_ENTRY` and its first instruction (`di`), **with BREAK held** and a **non-zero byte left in stock RAM at `RUNNING` (`$5EB6`)**, would make Leap-C's interrupt handler take BREAK and unwind to a run stack of 0. It was forced in a test and never seen otherwise: after the stock boot, `RUNNING` reads 0. A physical machine has not been tried.

## Qualification

`make test-cart` (`tools/carttest.py`, 160 cases with `CARTTEST_ARGS=--fuse`, about 2.5 minutes): the cartridge on ZEsarUX with the stock `ts2068.rom` against `RUN` on the release ROM (115 programs); 25 behaviour cases; a port audit; the hand-off; and 9 programs on Fuse 1.9.1 with its stock ROMs. Emulators only: the Z80, SCLD and DOCK models of two emulators say nothing about a real machine's timing, the DOCK's electrical behaviour, or a PicoROM. Reports from real hardware are welcome.
