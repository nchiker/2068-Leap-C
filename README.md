# 2068-Leap-C

**A C computer for the Timex Sinclair 2068.** Leap-C replaces the TS2068's ROMs with a full-screen C editor and a C compiler that runs on the machine itself: you type a program, `RUN` compiles it to native Z80 code in a moment, and it runs. No cross-compiler, no PC needed. It is built on the platform of [2068-Leap V2](https://github.com/nchiker/2068-Leap).

| ▶ [**Try it in your browser**](https://nchiker.github.io/TSRun/?rom=leapc) | ⬇ [**Download the beta**](https://github.com/nchiker/2068-Leap-C/releases) | 📖 [**User guide**](docs/USER_GUIDE.md) | 🧪 [**Beta testing**](docs/BETA_TESTING.md) |
|---|---|---|---|

```c
// expect: exit 0
// screen: 0 Hello, TS2068!
int main(void)
{
    cls();
    printf("Hello, TS2068!\n");
    return 0;
}
```

- **The language:** a documented subset of C89: `char`, `int`, `unsigned`, pointers, arrays, `struct`, `enum`, `typedef`, function pointers, recursion, `float`, every operator and statement, `#define`. What is not supported is reported as an error, never miscompiled.
- **The library:** text and colour, `printf`, the keyboard, graphics, the AY sound chip, time, strings, the heap, cassette data, built in with no `#include`. Libraries written in assembly load from tape (`LIB "shapes"`).
- **The machine:** an original 48 KB TS2068, unexpanded. About 18 KB for a program's source and 19 KB for its compiled code; compiling takes about 13 ms a line. Programs and data are saved on cassette.

## Status: public beta 1.0.0-beta.1

Leap-C is **feature-complete for release 1** and in **public beta**. It is qualified on two emulators, **Fuse 1.9.1** and **ZEsarUX 13.0** (with a patch), by thousands of automated tests. It has **not yet been run on a physical TS2068**: that, and your reports, come before release 1.0.

## Quick start (five minutes)

1. **Fastest:** open **[nchiker.github.io/TSRun/?rom=leapc](https://nchiker.github.io/TSRun/?rom=leapc)** in a web browser: the TS2068 with Leap-C, nothing to install (tapes do not load there).
2. **Or in an emulator:** download `leapc-1.0.0-beta.1-emulators.zip` from the [releases](https://github.com/nchiker/2068-Leap-C/releases) and unzip it. Install **Fuse 1.9.1** ([EMULATORS.md](docs/EMULATORS.md) §2.1: Windows has a ready-made build) and start it with Leap-C's ROMs (on Linux, as below; Windows and macOS: [EMULATORS.md](docs/EMULATORS.md) §2.2):

   ```sh
   fuse --machine ts2068 --rom-ts2068-0 /path/to/pack/roms/leapc_home.bin --rom-ts2068-1 /path/to/pack/roms/leapc_exrom.bin --no-traps --no-auto-load
   ```

3. A chord sounds and the editor appears: a white screen with `LINE 1/0` at the bottom.
4. Type the program above (without the `//` lines if you like), pressing Enter after each line. On a PC, **Ctrl** is SYMBOL SHIFT: Ctrl + P is `"`, Ctrl + O is `;`, Ctrl + F and Ctrl + G are `{` and `}`, Ctrl + D is `\`, Ctrl + 8 and 9 are `(` and `)`.
5. On the empty line after the last, type `RUN` and press Enter. The program prints its greeting; the report shows `EXIT 0`. Press a key to go back to the editor.

Then read the [user guide](docs/USER_GUIDE.md), try the [examples](docs/EXAMPLES.md), and see [BETA_TESTING.md](docs/BETA_TESTING.md) for what to try and how to report.

## Documents

| | |
|---|---|
| [docs/EMULATORS.md](docs/EMULATORS.md) | setting up Fuse, ZEsarUX and TSRun on Windows, macOS and Linux; the PC keyboard; tapes; troubleshooting |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | the editor, the commands, the C you can use, the library, errors, limits |
| [docs/EXAMPLES.md](docs/EXAMPLES.md) | Leap-C by example: 27 short programs (every one is a test) |
| [docs/BETA_TESTING.md](docs/BETA_TESTING.md) | what to test, how to report, known limitations |
| [docs/HARDWARE_CHECKLIST.md](docs/HARDWARE_CHECKLIST.md) | for a real TS2068: the EPROM images, tapes and checks |
| [spec.md](spec.md) | the full specification: ROM architecture, memory map, language, runtime, library, storage |
| [CONTRIBUTING.md](CONTRIBUTING.md) | building, testing and contributing |
| [project_plan.md](project_plan.md), [docs/milestones/](docs/milestones/) | how it was built, phase by phase, with every measurement |

## Reporting problems

Open an issue: **[Bug report](https://github.com/nchiker/2068-Leap-C/issues/new?template=bug_report.yml)** or **[Question or suggestion](https://github.com/nchiker/2068-Leap-C/issues/new?template=question.yml)**. Give the emulator and its version, your operating system, the ROM hashes, the program, the steps and a screenshot ([BETA_TESTING.md](docs/BETA_TESTING.md) §2).

## Building from source

Needs [sjasmplus](https://github.com/z00m128/sjasmplus) 1.23.1 and Python 3.11 or later:

```sh
make          # the ROM images in build/ (leapc_home.bin, leapc_exrom.bin, leapc_zesarux.bin) and the libraries
make check    # sizes, checks, the documentation's examples in step
make repro    # two clean builds give identical images
```

The emulator test suites need more ([CONTRIBUTING.md](CONTRIBUTING.md)).

## License

Leap-C is released under the [MIT License](LICENSE). The ROM images also contain a small part derived from the TS2068's own ROM (the cassette block routines and a block-graphics sequence), copyright Amstrad, which Amstrad allows to be redistributed free of charge; see [NOTICE](NOTICE) for this and for the code that comes from Leap V2 and ts2068-debug (both MIT). Leap-C is an independent community project, not affiliated with Timex, Sinclair or Amstrad.
