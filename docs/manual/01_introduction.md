# Leap-C -- User Manual and Language Reference

**For the Timex Sinclair 2068 with the Leap-C ROMs.**

*Edition for release 1.0.0-beta.2.* This manual describes 1.0.0-beta.2, the current public beta. It is emulator-qualified: it has been tested on Fuse 1.9.1 and on ZEsarUX 13.0 (with a small patch), and it has **not yet been run on a physical TS2068**. Where something depends on real hardware, the manual says so.

---

## Contents

| Part | What it is for |
|---|---|
| [Part 1, Introduction](01_introduction.md) | what Leap-C is, how to start it, how this manual works |
| [Part 2, Beginner's guide](02_beginners_guide.md) | a step-by-step course for someone who has never programmed in C: the editor, your first program, numbers, characters, decisions, loops, functions, arrays, pointers, structures, the screen, graphics, sound, the keyboard, floating point, tapes |
| [Part 3, Keywords](03_keywords.md) | every C keyword, preprocessor directive, operator group and shell command (`RUN`, `LIST`, `FREE`, `NEW`, `SAVE`, `LOAD`, `VERIFY`, `LIB`), A to Z, with examples |
| [Part 4, The library](04_library.md) | every built-in function, A to Z: text, colour, keyboard, graphics, sound, time, strings, memory, tape |
| [Part 5, Concepts](05_concepts.md) | the ideas behind the system, A to Z: arrays, BREAK, differences from standard C, errors, floating point, high resolution, memory, pointers, tapes, the editor ... |
| [Part 6, Loadable libraries](06_libraries.md) | `LIB`, the `shapes` library, and how to write a library of your own |
| [Part 7, Practical examples](07_examples.md) | complete programs to type in and change |
| [Appendices](08_appendices.md) | messages and reports, error codes, character set and keyboard, limits, memory map, hardware notes, keyword and function index, how this manual was checked |

The manual follows the plan of the *Sinclair QL User Guide*: a gentle beginner's guide, then a keyword reference and a concepts reference each in alphabetical order, with the tables at the back.

## What Leap-C is

The Timex Sinclair 2068 normally starts in the BASIC of its ROM. **Leap-C** replaces that ROM with a new one. You switch on and find a full-screen program editor. You type a program in the C language. You type `RUN`, and the machine itself compiles the program to native Z80 machine code, in a moment (about 13 milliseconds a line), and runs it. No cross-compiler is needed, and no PC.

Its main features:

* a full-screen **editor** with bold keywords and a status row;
* a documented subset of **C89** (ANSI C): `char`, `int`, `unsigned`, pointers, arrays of any dimension, `struct`, `enum`, `typedef`, function pointers, recursion, `float`, every operator and statement, `#define`;
* anything outside that subset is reported as an error, `NOT SUPPORTED`. It is never silently compiled wrongly;
* a **library** built into the ROM, needing no `#include`: text and colour, `printf`, the keyboard, graphics, the AY sound chip, time and random numbers, strings, the heap, and data on cassette tape;
* **floating-point** numbers in the Sinclair 5-byte format (`float` and `double` are the same type);
* programs saved to, loaded from and verified against **cassette tape** (`SAVE`, `LOAD`, `VERIFY`);
* **libraries written in assembly** that load from tape (`LIB "shapes"`) and add functions to the language.

It runs on an ordinary 48 KB TS2068, unexpanded. There is room for about 18 KB of program text and about 19 KB of compiled code and data. The exact limits are in the concept [Memory](05_concepts.md#memory) and in Appendix E.

Leap-C is built on the platform of 2068-Leap V2, a BASIC for the same machine. It is a different language. The two do not share programs or tapes, and nothing in this manual is about BASIC.

## The status of this release

Release 1.0.0-beta.2 is a **public beta**. It is feature-complete for release 1, and it has been tested by thousands of automated tests on two emulators: Fuse 1.9.1 and ZEsarUX 13.0 (with a patch). It has **not been run on a physical TS2068**, a real cassette recorder or a real keyboard. Your reports come before release 1.0; [BETA_TESTING.md](../BETA_TESTING.md) says what to try and how to report.

Every complete program in this manual that carries `// expect:` lines is an automated test. The build compiles and runs it on the ROMs and checks that it does what its comments say (see [Appendix I](08_appendices.md)).

## Starting it

**In a web browser.** The quickest way: open <https://nchiker.github.io/TSRun/?rom=leapc>. You get the TS2068 with Leap-C, with nothing to install. Tapes do not load there.

**On an emulator.** Download `leapc-1.0.0-beta.2-emulators.zip` from the [releases page](https://github.com/nchiker/2068-Leap-C/releases). It holds three ROM files:

| File | What it is | Used by |
|---|---|---|
| `roms/leapc_home.bin` | the HOME ROM, 16,384 bytes | Fuse: ROM 0 |
| `roms/leapc_exrom.bin` | the EXROM (extension ROM), 8,192 bytes | Fuse: ROM 1 |
| `roms/leapc_zesarux.bin` | the two in one file, 24,576 bytes | ZEsarUX: `--romfile` |

The recommended emulator is **Fuse 1.9.1**, which needs no changes. **ZEsarUX 13.0** works only with a small patch: the downloadable 13.0 shows a blank screen. The [emulator setup guide](../EMULATORS.md) describes both, on Windows, macOS and Linux, and says how to type C on a PC keyboard. For Linux and Fuse the command is:

```
fuse --machine ts2068 --rom-ts2068-0 /path/to/pack/roms/leapc_home.bin --rom-ts2068-1 /path/to/pack/roms/leapc_exrom.bin --no-traps --no-auto-load
```

Use full paths to the ROM files. Switch on, and a chord sounds and the editor appears.

**On a TS2068.** The release has a hardware kit with the ROMs as EPROM images (a 27128 for the HOME ROM and a 2764 for the EXROM), check programs and a checklist; see [HARDWARE_CHECKLIST.md](../HARDWARE_CHECKLIST.md). Nothing about real hardware has been tested.

**Tapes.** Programs and libraries come as `.tzx` and `.tap` files for an emulator's tape interface. Leap-C's tapes carry their own version word, so the TS2068's BASIC and Leap V2 refuse them, and Leap-C refuses theirs (`BAD TAPE VERSION`). The concept [Tapes](05_concepts.md#tapes) and the emulator guide say how to work a tape.

**The keyboard.** The TS2068 has two shift keys: CAPS SHIFT (capitals and the editing keys) and SYMBOL SHIFT (punctuation). On a PC, **Shift** is CAPS SHIFT and **Ctrl** is SYMBOL SHIFT. C needs a lot of punctuation; the table is in the concept [The editor](05_concepts.md#the-editor) and in Appendix D.

## How to read this manual

* **Type the examples.** They are small. Change numbers and words and see what happens.
* In the text, `PROGRAM TEXT AND COMMANDS` are in a typewriter face. C is **case-sensitive**: `main` is not `Main`. The shell commands (`RUN`, `LIST`, ...) may be typed in either case.
* A box of C is a **program** or a piece of one. Type each line on its own line. A box that is a whole program starts with comment lines that begin `// expect:`, `// screen:` and so on. To the compiler they are ordinary comments, so you can type the program with or without them. They state what the automated test checks:

| Line | Meaning |
|---|---|
| `// expect: exit N` | `main` returns N: the number after `EXIT` in the report |
| `// expect: error E_NAME L` | the compile stops with that error at line L (lines count from 1, the first line of the box, comments included) |
| `// expect: rterror N` | the program stops with runtime error N |
| `// screen: R TEXT` | text row R (0 is the top) reads TEXT |
| `// attr: R C V`, `// pixel: X Y V` | a cell's attribute byte; a pixel (counted from the top left) |
| `// keys: ...` | the keys "typed" while the program reads the keyboard |
| `// library: NAME` | the library NAME is loaded first, as `LIB "NAME"` loads it |

* A box with no title and no `//` lines, in a plain frame, shows **exactly** what appeared on the screen. In a listing of a whole screen, a line of three dots (`...`) stands for any number of blank rows.
* A fragment (a few lines that are not a whole program) is a box of C with no `// expect:` line. It is for reading, not for typing as it stands.
* Words in *italics* in a syntax line are things you supply.
* The reference parts are in alphabetical order. Where something has two names (a keyword and the concept it belongs to) each points to the other.

## If you know C

Leap-C is a subset of C89 for a 16-bit machine, with a few extensions. `int` is 16 bits and wraps around; `char` is **unsigned**; `float` and `double` are one type, the Sinclair 5-byte format, not IEEE. `//` comments are accepted. There is no `long`, `union` or `volatile`, no struct parameters, return values or assignment (use pointers and `memcpy`), no initialisers on local arrays and structures (declare them `static`), no function-like macros, `#if` or `#include` of another file, no variadic functions of your own, and only one source file. `printf` has `%d %u %x %c %s %f %%` and a width, but no flags and no `%e`. There is no maths library. Integer division by zero gives 0 without an error, and array bounds and NULL pointers are not checked. No `#include` is needed: the library is built in. The full list is the table in the concept [Differences from standard C](05_concepts.md#differences-from-standard-c).

If you have never written C, begin with [Part 2](02_beginners_guide.md).
