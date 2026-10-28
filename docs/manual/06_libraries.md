# Part 6 -- Loadable libraries

The C that is built into the ROM is complete for programs, text, graphics, sound and tapes (see [Part 4](04_library.md) for the built-in functions). Everything more specialised can live in a **library**: a small piece of machine code on tape that adds **functions** to the language. Leap-C is extended through functions, not through new syntax, so a library needs nothing new in the compiler: a program calls its functions exactly as it calls `printf` or `plot`, with no declaration and no `#include`.

The release comes with one library:

| Library | Tape name | Size | Functions it adds |
|---|---|---|---|
| **shapes** | `shapes` | 438 bytes | `circle`, `box`, `isqrt` |

You can also write your own; the last section of this part says how.

## Loading a library

Type, on the editor's empty last line,

```
LIB "shapes"
```

and start the tape. The status row shows `LOADING`, then `LOADING shapes` when the tape's header has been found, and at the end the report

```
LIBRARY shapes: 3 FUNCTIONS
SOURCE 120 B  FREE 18292 B
```

(the second row, as for the tape commands, is the size of your program and the room left for it; the numbers here are only an example). Press a key to go back to the editor. The three functions can be used from then on.

`LIB ""` loads the next library tape on the cassette whatever its name, as `LOAD ""` does for programs. The name of a library is 1 to 10 characters; the report shows the name that the tape carries.

The commands, like the other shell commands, are typed alone on the empty last line, in capitals or small letters. Where to find the tape, and how to play it into each emulator, is in `docs/EMULATORS.md`, section 7.2; the file is `shapes.tzx` (or `.tap`), which `make libs` builds in `build/libs/` along with a `.wav`, and the hardware kit has it as `tapes/l1_shapes`.

The rules:

* **One library at a time.** A library occupies image region 3, a 1 KB window of memory (`$F400-$F7FF`). Loading another library **replaces** the first: its functions stop working.
* **The library stays.** `NEW`, `LOAD` and `RUN` do not unload it: it belongs to the machine's session, not to the program in the editor, so a program that you `LOAD` from tape can use it at once. (Leap V2's `NEW` unloaded its package; Leap-C's does not.)
* **`LIB` alone unloads it.** Type `LIB` on the empty last line; the status row shows `NO LIBRARY` until a key is pressed.
* **A reset clears it.** After a reset or switching on, no library is loaded.
* **It costs program space.** While a library is loaded its 1 KB is region 3 of the compiled program's memory (see [Memory](05_concepts.md#memory)), so the program is compiled into the other regions and the largest program you can run is 1 KB smaller. The `IMAGE` size in the `RUN` report does not count the library.
* **Calling it needs no declaration.** A name that your program does not declare is looked up in the ROM's own library, and then in the loaded library. If you declare a function of the same name yourself, your declaration wins. A name that both the ROM and the library have is the ROM's function; the library's is never called.
* **Calls are checked.** A library function has a prototype, so a call with the wrong number of arguments is `ERROR 55: WRONG ARGUMENT COUNT`, and a pointer given for an `int` parameter is `ERROR 40: TYPE MISMATCH`.
* **Library tapes are their own kind.** `LOAD`, `VERIFY` and `tape_load()` skip library tapes, and `LIB` skips program tapes and data tapes (see [Tapes](05_concepts.md#tapes)).
* **BREAK** or SPACE stops a `LIB` that is waiting for a tape (report `BREAK`). Left alone, `LIB` gives up after about two minutes without a tape (`LOAD FAILED`).

The reports of `LIB`:

| Report | Meaning |
|---|---|
| `LIBRARY name: n FUNCTIONS` | the library arrived whole; *name* is the tape's, *n* the number of functions |
| `BAD TAPE VERSION` | the tape is not a Leap-C library (it is a V2 package, a program, a stock BASIC tape, or a library built for a later release): refused at its header, nothing written |
| `LOAD FAILED` | no library tape was found before the search gave up, or its length is more than 1,024 bytes, or a block was damaged |
| `BREAK` | SPACE or BREAK stopped it |
| `BAD NAME` | more than 10 characters, no closing quote, or something after the quote |
| `NO LIBRARY` | (for `LIB` alone) the library was unloaded |

A failure that had already begun writing into region 3 (a damaged block, or BREAK, during the library's data) leaves **no** library loaded; any other failure leaves the library that was loaded before.

## Errors

A library function that is not loaded is simply an undefined function: the compile stops with `ERROR 70: UNDEFINED FUNCTION`, and the second report row names the function (`LINE 4  'circle'`).

```c
// expect: error E_UNDEFFN 4
int main(void)
{
    circle(128, 96, 10);
    return 0;
}
```

With the library loaded, a call with the wrong number of arguments does not compile:

```c
// library: shapes
// expect: error E_ARGS 5
int main(void)
{
    circle(128, 96);
    return 0;
}
```

A library may stop a program with a runtime error. It is reported as for the built-in functions, at the line where the function that called the library begins (see [Errors](05_concepts.md#errors)). The shapes library does so for a negative radius:

```c
// library: shapes
// expect: rterror 4
// rtline: 4
int main(void)
{
    circle(128, 96, -1);
    return 0;
}
```

(The `// library: shapes` line is not C: it is the instruction that makes the automated test load the library before it compiles the program, as `LIB "shapes"` does. See [Appendix I](08_appendices.md#appendix-i-how-this-manual-was-checked). The `//` lines are comments to the compiler.)

---

## The shapes library

`LIB "shapes"` adds three functions.

| Function | Does |
|---|---|
| `void circle(int x, int y, int r)` | draws a circle of radius *r* about the pixel *x*, *y* |
| `void box(int x0, int y0, int x1, int y1)` | draws the four sides of a rectangle |
| `unsigned isqrt(unsigned n)` | the integer square root of *n* |

`circle` and `box` draw like `plot()`: pixels are numbered from the top left (x 0 to 255, y 0 to 191), the ink is the current `ink`, the cell gets the print attribute, and `over(1)` makes them draw by exclusive-or. Each point is drawn **exactly once**, so with `over(1)` a second identical call erases what the first drew.

## circle
[library: shapes]

`void circle(int x, int y, int r)` -- **library function**

Draws the outline of a circle of radius *r* pixels, centred on the pixel *x*, *y* (the midpoint algorithm, all eight octants). It draws in the print attribute and in `over` mode like `plot()`, each point once. Points that fall off the screen are left out, so a circle can run off an edge. A negative radius is runtime error 4 (`BAD ARGUMENT`).

```c
// library: shapes
// expect: exit 0
// screen: 0 CIRCLE
// pixel: 148 96 1
// pixel: 108 96 1
// pixel: 128 76 1
// pixel: 128 116 1
// pixel: 128 96 0
int main(void)
{
    cls();
    print("CIRCLE");
    circle(128, 96, 20);
    return 0;
}
```

The four points where the circle crosses the horizontal and vertical lines through its centre are set, and the centre itself is not.

```c
// library: shapes
// expect: exit 0
// pixel: 140 100 1
// pixel: 100 60 1
// pixel: 60 100 1
// pixel: 100 140 1
// pixel: 247 3 1
// pixel: 253 9 1
// pixel: 100 100 0
int main(void)
{
    cls();
    circle(100, 100, 40);
    circle(253, 3, 6);
    return 0;
}
```

The second circle, centred near the top right corner, has points off the screen (its top is at y = -3 and its right side at x = 259). They are left out, without an error; the rest of it is drawn.

**See also** [box](#box), [plot](04_library.md#plot), [draw](04_library.md#draw), [over](04_library.md#over), [ink](04_library.md#ink).

---

## box
[library: shapes]

`void box(int x0, int y0, int x1, int y1)` -- **library function**

Draws the four sides of the rectangle with opposite corners *x0*, *y0* and *x1*, *y1*, each point once, in the print attribute and in `over` mode like `plot()`. The corners may be given in either order. A coordinate that is off the screen is moved to its edge, as `draw()` does, so `box(-5, -5, 300, 200)` draws the edge of the screen.

```c
// library: shapes
// expect: exit 0
// screen: 0 BOX
// pixel: 60 40 1
// pixel: 196 152 1
// pixel: 60 100 1
// pixel: 196 100 1
// pixel: 128 40 1
// pixel: 128 152 1
// pixel: 128 100 0
int main(void)
{
    cls();
    print("BOX");
    box(196, 152, 60, 40);
    return 0;
}
```

(The corners are given upside down on purpose.) Off the screen:

```c
// library: shapes
// expect: exit 0
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 255 0 1
// pixel: 0 191 1
// pixel: 128 0 1
// pixel: 128 96 0
int main(void)
{
    cls();
    box(-5, -5, 300, 200);
    return 0;
}
```

**See also** [circle](#circle), [draw](04_library.md#draw), [plot](04_library.md#plot).

---

## isqrt
[library: shapes]

`unsigned isqrt(unsigned n)` -- **library function**

The integer square root of *n*: the largest whole number *r* with *r* x *r* not more than *n*. The result is 0 to 255 (the root of 65535 is 255). A negative `int` given as *n* is read as the `unsigned` number with the same bits.

```c
// library: shapes
// expect: exit 12
// screen: 0 12 12 13
int main(void)
{
    cls();
    printf("%u %u %u", isqrt(144), isqrt(168), isqrt(169));
    return isqrt(150);
}
```

(168 is one less than 13 x 13, so its root is 12.)

**See also** [abs](04_library.md#abs), [Floating point](05_concepts.md#floating-point).

---

## Writing your own library

A library is written in **Z80 assembly** and built on a PC; it cannot be written on the TS2068 itself in this release. What is described here is the interface. It is defined, exactly, by `include/leapc_lib.inc` in the repository; the tool that builds the tape is `tools/lib2tape.py`; the example to copy is `libs/shapes.asm`; `spec.md` section 2.4 (the services), 7.2 (the library) and 8.4 (the tape) have the details.

### The image

A library is an **image** for region 3, `$F400-$F7FF`, at most 1,024 bytes. It starts with a header, then the table of the functions it exports, then its code and data:

| Offset | Bytes | Contents |
|---|---|---|
| 0 | 1 | the magic `$8D`: bit 7 says "Leap", and `$0D` says "a Leap-C library" (program and data tapes have `$8C`) |
| 1 | 1 | the ABI version the library needs (1 in this release) |
| 2 | 1 | the number of exported functions, 1 to 99 |
| 3 | | the export table: for each function its name, its address (2 bytes, inside the image) and its signature byte; the table ends with a 0 |
| | | the code and data |

A name is 1 to 31 characters of a C identifier (not a C keyword), with **bit 7 set on its last character**. The ROM's own function names cannot be hidden: if your library exports a name that the built-in library has, the ROM's function is the one that a program gets, and `lib2tape.py` says so.

The **signature byte** has the return type in its high four bits and the parameter list in its low four:

| Return type | Code | Parameter list | Code |
|---|---|---|---|
| `void` | 0 | no prototype (any arguments, the default promotions; a `float` is a 3-word slot) | 0 |
| `char` | 1 | `()` | 1 |
| `int` | 3 | `(int)` | 2 |
| `unsigned` | 4 | `(void *)` | 3 |
| `float` (the result in `F_ACC`) | 5 | `(int, int)` | 4 |
| `void *` | 8 | `(void *, int)` | 5 |
| `char *` | 9 | `(void *, void *)` | 6 |
| | | `(void *, void *, int)` | 7 |
| | | `(void *, int, int)` | 8 |
| | | `(int, void *, int)` | 9 |
| | | `(int, int, int, int)` | 10 |
| | | `(int, int, int, int, void *)` | 11 |
| | | `(int, int, int)` | 12 |
| | | `(int, void *)` | 13 |
| | | `(int, int, void *)` | 14 |
| | | `(int, int, int, int, int)` | 15 |

An integer parameter is an `int`; a pointer parameter is `void *`, to which any object pointer converts. The assembler macros `LX_HEADER`, `LX_EXPORT` and `LX_EXPORTS_END`, and the names `LXR_*` (return types) and `LXP_*` (parameter lists), build all this. The start of `libs/shapes.asm` shows it whole:

```asm
    INCLUDE "leapc_lib.inc"
    ORG  LX_BASE
    LX_HEADER 3
    LX_EXPORT "circle", circle, LXR_VOID, LXP_III
    LX_EXPORT "box", box, LXR_VOID, LXP_IIII
    LX_EXPORT "isqrt", isqrt, LXR_UINT, LXP_I
    LX_EXPORTS_END
```

### Writing a function

* A function is called with the **C calling convention**: the arguments are on the stack, the first lowest, and the caller removes them. The result is returned in HL (in `F_ACC` for a `float`). The function keeps IX and IY and may destroy AF, BC, DE and HL.
* It must **call `LX_ARGS` first**. That returns the first three arguments in HL, DE and BC (a fourth and later ones are on the stack, at SP + 8, + 10 and so on) and records the place in the program where the function was called, so that a runtime error, or BREAK, in the function (or in a service it uses) is reported at the right line of the program.
* It reaches the ROM **only through a table of jumps**, 16 slots of 3 bytes at `$3FD0-$3FFF`, the last bytes of the HOME ROM. The table never moves, so a library built against it runs on every ROM that keeps it. ABI 1 has these services:

| Slot | Name | Service | In | Out |
|---:|---|---|---|---|
| 0 | `LX_ARGS` | the arguments (call it first) | the return address and arguments on the stack | HL, DE, BC = the first three arguments |
| 1 | `LX_PUTC` | print a character at the print position | A | |
| 2 | `LX_PUTS` | print a string at the print position | HL = the NUL-terminated text | |
| 3 | `LX_MALLOC` | a heap block, as `malloc` | HL = the size | HL = the block, or 0 |
| 4 | `LX_FREE` | free a heap block, as `free` | HL = the block (0: nothing) | |
| 5 | `LX_MUL` | 16-bit multiply | DE, HL | HL = DE x HL |
| 6 | `LX_DIVS` | signed divide, toward zero (0 for a divisor of 0) | DE, HL | HL = DE / HL |
| 7 | `LX_DIVU` | unsigned divide | DE, HL | HL = DE / HL, DE = DE % HL |
| 8 | `LX_FOP` | an operation of the float core on `F_ACC` | A = the operation `FOP_*` | `F_ACC` (see below) |
| 9 | `LX_ERROR` | end the program with a runtime error | A = the error | does not return |
| 10 | `LX_KEY` | wait for a key (BREAK ends the program) | | A = its code |
| 11 | `LX_INKEY` | the key latched since the last read | | A = its code, or 0 |
| 12 | `LX_FRAMES` | the frame counter | | HL |
| 13 | `LX_PLOT` | a pixel in the print attribute and `over` mode; off the screen, nothing | HL = x, DE = y | |
| 14, 15 | | reserved: a call is runtime error 4 | | |

What each slot destroys is in `spec.md` section 2.4. The float operations are `FOP_FRI` 0 (`F_ACC` = the integer in HL), `FOP_FRU` 1 (HL as `unsigned`), `FOP_TOI` 2 (HL = `F_ACC` truncated), `FOP_NEG` 3, `FOP_FTOA` 8 (HL = the text of the float at HL with C decimals), and the binary operations `FOP_ADD` `$80`, `FOP_SUB` `$82`, `FOP_SUBR` `$83`, `FOP_MUL` `$84`, `FOP_DIV` `$86`, `FOP_DIVR` `$87`, `FOP_CMP` `$88`: they compute `(HL) op F_ACC` (the reversed ones `F_ACC op (HL)`), HL being the address of the left operand's 5 bytes. A float overflow raises runtime error 6 at the program's call.

* A library can use these **pinned names**: `F_ACC` (`$5ED6`, the float accumulator, 5 bytes), `LIB_COL` and `LIB_ROW` (`$5EC2`, `$5EC3`: the print position), `LIB_ATTR` (`$5EC8`: the print attribute), and the runtime errors `RTE_HEAP` 2, `RTE_ARG` 4 and `RTE_FLOAT` 6. It can name nothing else of the ROM.
* A function's **own cells** are in its image, after its code. They keep their values between calls **and between runs**: region 3 is not cleared.
* It may use no more stack below its arguments than the ROM's own library does, the services it calls included: the margin is 40 bytes (`circle` and `box` use 30).
* The ABI is fixed. A slot is never moved or reused; a new service takes the next reserved slot and raises the ABI version by one. A library names the ABI it needs, and `LIB` refuses one that needs more than the ROM has (`BAD TAPE VERSION`).

The start of `isqrt` in `libs/shapes.asm`, as an illustration (the rest of the function is a loop on the bits of *n*; the whole library is 438 bytes):

```asm
isqrt:
    call LX_ARGS                       ; HL = n
    ...
    ex   de, hl                        ; HL = r
    ret
```

### Building and loading it

`tools/lib2tape.py` needs Python 3.11 or later and the assembler `sjasmplus` (version 1.23.1: see `CONTRIBUTING.md`). Give it the source and one or more outputs; the extension of each says what it is:

```
python3 tools/lib2tape.py mylib.asm mylib.bin mylib.sym mylib.tap mylib.tzx mylib.wav
```

`.tap` and `.tzx` are tape files for emulators and tape players, `.wav` is an audio file for the EAR socket, `.bin` is the image itself and `.sym` lists its labels. The name of the tape is that of the source file; `--name NAME` chooses another (1 to 10 characters of ASCII 32 to 126, no quote). The tool refuses a library whose image is more than 1,024 bytes, whose magic or ABI is wrong, whose export count is not 1 to 99, whose names are not C identifiers of 1 to 31 characters, whose addresses are not inside the image, whose signature uses an unknown return type, or whose table does not end with 0.

The tape is the two blocks of a program tape, with these differences:

| Field | Value |
|---|---|
| header type | 4 |
| name | 1 to 10 characters, padded with spaces |
| length | the image's, 1,024 bytes at most |
| version word | the image's magic and ABI: `$8D01` |
| data block | the image, verbatim |

The version word is how `LIB` decides: another magic, or an ABI above the ROM's, is `BAD TAPE VERSION` at the header, before a byte is written. Leap V2's package tapes have the same header type but a different version word, and are refused the same way (and Leap V2 refuses Leap-C's library tapes).

Then `LIB "mylib"` loads it and your functions are at your program's service. Writing a library in C on the machine itself (`#pragma library`, `SAVE "name" LIB`) is not part of this release.
