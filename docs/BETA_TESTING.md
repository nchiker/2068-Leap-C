# Testing the Leap-C beta

Thank you for trying **Leap-C 1.0.0-beta.2**, a C compiler and editor in the ROMs of the Timex Sinclair 2068. The beta is for finding what the project's own tests missed before release 1.0. Most of you will use an emulator; a few may have a real TS2068.

**Status.** Leap-C is qualified on two emulators, Fuse 1.9.1 and ZEsarUX 13.0 (with a patch), by thousands of automated tests: every C program of its test corpus, the editor, tapes, BREAK, power-on memory patterns. It has **not yet run on a physical TS2068**: if you have one, your results are especially valuable (section 5).

You need: an emulator set up as [EMULATORS.md](EMULATORS.md) describes, and the emulator pack (`leapc-1.0.0-beta.2-emulators.zip`) from the [release page](https://github.com/nchiker/2068-Leap-C/releases). [USER_GUIDE.md](USER_GUIDE.md) explains Leap-C itself.

## 1. What to try

Anything you like. These are the areas where reports help most; tick off what you tried in your report.

1. **Start-up.** Set up your emulator from [EMULATORS.md](EMULATORS.md) *without help*. Did the instructions work for your system? Where did you get stuck? This is as useful as a bug report.
2. **Write and run programs.** Type the [user guide](USER_GUIDE.md)'s programs, then your own: games, puzzles, number crunching, graphics, sound. Leap-C should compile any program in its C subset ([USER_GUIDE.md](USER_GUIDE.md) §4) and report anything else as an error, never crash or produce wrong results silently.
3. **The examples.** [EXAMPLES.md](EXAMPLES.md) has 27 short programs and the user guide 6; the pack has each as a tape (`tapes/examples/exNN` and `ugNN`, listed in `TAPES.md`). Open one tape file at a time, `LOAD ""` and `RUN` it. Each one's first lines (`// expect:`, `// screen:`) say what it should show. Example 27 (`ex27`) and the guide's library program (`ug05`) need `LIB "shapes"` first.
4. **The editor.** Long lines that wrap, editing in the middle of a line, DELETE, inserting and deleting lines, moving around a long program, `LIST`, keyword highlighting. Does anything get lost, misplaced or drawn wrongly?
5. **Errors.** Make mistakes on purpose: a missing `;`, a misspelt name, a wrong type. Is the error message right? Is the cursor where the problem is? Runtime errors: deep recursion, `beep(1, 100)`. BREAK (CAPS SHIFT + SPACE) in a running program.
6. **Tapes** (Fuse for saving: [EMULATORS.md](EMULATORS.md) §7). `SAVE "name"`, then `NEW` and `LOAD "name"`; `VERIFY`; programs that use `tape_save()` and `tape_load()`; a tape made on your PC with `tools/c2tape.py` (from the repository: [EMULATORS.md](EMULATORS.md) §7.4).
7. **The shapes library.** `LIB "shapes"` from `libs/shapes.tzx`, then `circle()`, `box()` and `isqrt()` ([USER_GUIDE.md](USER_GUIDE.md) §9). `LIB` alone to unload it.
8. **Limits.** Large programs, deep recursion, big arrays, many functions: what happens near the limits ([USER_GUIDE.md](USER_GUIDE.md) §11)? `FREE` shows the space left.
9. **The documents.** Anything wrong, unclear or missing in the guides.

## 2. Reporting

Open an issue at **[github.com/nchiker/2068-Leap-C/issues](https://github.com/nchiker/2068-Leap-C/issues)** and choose **Bug report** or **Question or suggestion**. Please check the open issues and section 3 first.

A good bug report has:

| | |
|---|---|
| **The ROMs** | their SHA-256 hashes (HOME `043becf4...`, EXROM `97fe9523...` for this beta; [EMULATORS.md](EMULATORS.md) §1 shows how to check) |
| **The emulator** | its name and exact version (Fuse 1.9.1, ZEsarUX 13.0 with the patch, TSRun, ...), and how you started it (the command line, or the settings you changed) |
| **Your computer** | the operating system and its version (Windows 11, macOS 15, Ubuntu 24.04, ...) |
| **The program** | the program's text (as text, in a code block), or its tape file attached (zip it: GitHub takes `.zip`) |
| **The steps** | what you typed or pressed, from a fresh start, as a numbered list |
| **What happened** | and what you expected instead; the exact message and line from the report rows |
| **A screenshot** | the emulator's window (your system's screenshot key; or Fuse: **File → Screenshot → Save Screen as SCR...**; ZEsarUX: **Display → Save Screen**) |

The shortest program that shows the problem is the most useful. If you can, say whether it also happens in the other emulator.

## 3. Known limitations

These are known and need no report (unless you find they matter more than we thought):

- **No physical TS2068 has run Leap-C yet.** Timing on real hardware (contended memory, the 60 Hz frame), real cassette recorders and the real keyboard are unverified.
- **ZEsarUX:** the downloadable 13.0 shows a blank screen; it needs the patched build ([EMULATORS.md](EMULATORS.md) §3). ZEsarUX cannot write Leap-C's `SAVE` to a tape file. It runs the TS2068 at 50 frames a second instead of 60, so `pause()`, `frames()` and `beep()` last 20% longer there.
- **TSRun** (browser): tapes do not load, and `SAVE` cannot be recorded.
- **The language** is a C89 subset: no `long`, `union`, struct parameters or assignment, local array initialisers, function-like macros or `#if`, no maths library, `printf` without flags or `%e`/`%g` ([USER_GUIDE.md](USER_GUIDE.md) §4). Integer division by zero gives 0.
- **Key legends:** the keys for `[ ] { } | ~ ^ \` (SYMBOL SHIFT + Y U F G S A H D) have BASIC keywords printed on a real TS2068's keyboard, not these characters.
- **One program at a time**, in one source file, with about 18 KB for its source; one library at a time, of at most 1 KB.
- Leap-C reads only its own tapes: TS2068 BASIC and Leap V2 tapes give `BAD TAPE VERSION`.
- **Untested emulators** (EightyOne, other Fuse or ZEsarUX versions, Fuse for macOS, others): reports are welcome, but we have no instructions for them.

## 4. Beyond bugs

Questions, ideas and wishes are welcome as **Question or suggestion** issues: what was hard, what you missed, what you would build with it. Release 1.0's manuals will be written from this feedback.

## 5. On a real TS2068

If you have a TS2068 with an EPROM programmer (or EPROM cartridges), the release also has a **hardware kit** (`leapc-1.0.0-beta.2-hardware-kit.zip`): the ROMs as EPROM images for a 27128 (HOME) and a 2764 (EXROM) with Intel HEX files and checksums, check programs and examples as `.tap`, `.tzx` and `.wav` (to play into the EAR socket), and **[HARDWARE_CHECKLIST.md](HARDWARE_CHECKLIST.md)**: what to check, and what each check program should show (as both emulators showed it). Work through as much of the checklist as you can, and report each result, a pass too, with the item's number. The kit's ROM images contain code derived from the stock TS2068 ROM, which Amstrad allows to be redistributed free of charge: they are not for sale ([NOTICE](../NOTICE)).

Please be careful with your hardware: swapping ROMs means opening the machine, and we cannot be responsible for damage.
