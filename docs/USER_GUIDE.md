# Leap-C user guide

**Version 1.0.0-beta.2.** Leap-C turns a Timex Sinclair 2068 into a C computer: you type a program in a full-screen editor, and `RUN` compiles it to Z80 machine code on the machine itself and runs it. This guide covers what you need to use it. [EMULATORS.md](EMULATORS.md) sets up an emulator; [EXAMPLES.md](EXAMPLES.md) has more programs; [spec.md](../spec.md) is the full specification; the [user's manual](USER_MANUAL.md) covers everything at length.

Every program in this guide with `// expect:` lines is a test: the build runs it on the ROMs and checks the results those lines state. The `//` lines are ordinary comments to the compiler, so you can type the programs with or without them.

## Contents

1. [The first program](#1-the-first-program)
2. [The editor and its keys](#2-the-editor-and-its-keys)
3. [Commands and reports](#3-commands-and-reports)
4. [The C you can use](#4-the-c-you-can-use)
5. [The built-in library](#5-the-built-in-library)
6. [Floating point](#6-floating-point)
7. [Graphics, sound and the keyboard](#7-graphics-sound-and-the-keyboard)
8. [Tapes](#8-tapes)
9. [Loading a library](#9-loading-a-library)
10. [Error reports](#10-error-reports)
11. [Limits](#11-limits)

## 1. The first program

After the start chord the screen is white with the status row `LINE 1/0` at the bottom ([EMULATORS.md](EMULATORS.md) §5). Type this, pressing ENTER at the end of each line (SYMBOL SHIFT + P is `"`, SYMBOL SHIFT + O is `;`, SYMBOL SHIFT + F and G are `{` and `}`, SYMBOL SHIFT + D is `\`; the full table is in §2):

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

Then type `RUN` on the empty line after the last and press ENTER. The status row shows `COMPILING` for a moment, the program runs, and two report rows appear at the bottom:

```
Hello, TS2068!

...
EXIT 0
IMAGE 39 B  HEAP 18340 B
```

`EXIT 0` is what `main` returned; `IMAGE` is the size of the compiled program, `HEAP` the memory `malloc()` could have used. Press a key to go back to the editor, with your program as it was.

Things to know from the start:

- **No `#include` is needed.** `printf` and the rest of the library are built in; `#include <leap.h>` is accepted and does nothing.
- **Indent with spaces** (there is no TAB key). Lines are up to 127 characters; a long line wraps on the screen.
- **C is case-sensitive**: `main`, not `Main`. Keywords turn **bold** when you leave a line.
- A program starts with the screen as the editor left it: call `cls()` before printing.

## 2. The editor and its keys

The editor shows your program on rows 0-22; row 23 is the status row (`LINE n/m`: the cursor's line, and the number of lines). You edit one line at a time: type, move with the cursor keys, and ENTER stores the line. Moving off a line with UP or DOWN also stores it.

| Key (on a PC: [EMULATORS.md](EMULATORS.md) §6) | Does |
|---|---|
| letters, digits, SPACE | type; CAPS SHIFT + letter gives a capital |
| SYMBOL SHIFT + key | punctuation (table below) |
| ENTER | store the line and go to the next |
| CAPS SHIFT + 5 / 8 | cursor left / right |
| CAPS SHIFT + 7 / 6 | cursor up / down (between the rows of a wrapped line first) |
| CAPS SHIFT + 0 (DELETE) | delete the character before the cursor; on an empty line, delete the line |
| CAPS SHIFT + 1 | delete the whole line |
| CAPS SHIFT + ENTER | insert an empty line before this one |
| BREAK (CAPS SHIFT + SPACE) | stop a running program, a listing or a tape command |

SYMBOL SHIFT characters (the first eight are Leap-C's own; the rest are the TS2068's):

| `[` Y | `]` U | `{` F | `}` G | `\|` S | `~` A | `^` H | `\` D |
|---|---|---|---|---|---|---|---|
| `!` 1 | `@` 2 | `#` 3 | `$` 4 | `%` 5 | `&` 6 | `'` 7 | `(` 8 |
| `)` 9 | `_` 0 | `"` P | `;` O | `:` Z | `<` R | `>` T | `?` C |
| `=` L | `+` K | `-` J | `*` B | `/` V | `,` N | `.` M | |

## 3. Commands and reports

A command is typed **alone on the empty line after the last line** of the program, in upper or lower case. Anything else you type there becomes a new program line.

| Command | Does | Reports (rows 22-23, until you press a key) |
|---|---|---|
| `RUN` | compile, then run | `EXIT n` and `IMAGE i B  HEAP h B`; or a compile error, a runtime error or `BREAK` (§10) |
| `LIST` | show the program a page at a time | a key shows the next page; BREAK ends it |
| `FREE` | show the memory | `SOURCE s B  FREE f B` (the program's size and the room left for it) and `IMAGE i B  HEAP h B` (the last compiled program) |
| `NEW` | clear the program | (a loaded library stays) |
| `SAVE "name"` | save the program to tape (name: 1-10 characters) | `SAVED name`; `BREAK`; `BAD NAME`; `NO PROGRAM` (nothing to save) |
| `LOAD "name"`, `LOAD ""` | load a program from tape (`""`: the next one) | `LOADED name`; `LOAD FAILED`; `BAD TAPE VERSION` (not a Leap-C tape); `BREAK`; `BAD NAME` |
| `VERIFY "name"`, `VERIFY ""` | check a tape against the program | `VERIFIED name`; `VERIFY FAILED`; `BAD TAPE VERSION`; `BREAK`; `BAD NAME` |
| `LIB "name"`, `LIB ""` | load a library from tape (§9) | `LIBRARY name: n FUNCTIONS`; `BAD TAPE VERSION`; `LOAD FAILED`; `BREAK`; `BAD NAME` |
| `LIB` | unload the library | `NO LIBRARY` |

The tape commands' second report row is `SOURCE s B  FREE f B`. While a tape moves, the status row shows `SAVING name`; `LOADING` (or `VERIFYING`) while it searches, then `LOADING name` (`VERIFYING name`) once the tape's header is found. A failed `LOAD` keeps your program (except when part of a longer program had already replaced it: then the program is empty, as after `NEW`).

**After a report, press a key once every key is up**: Leap-C ignores a key still held from the command, so a report cannot vanish before you read it.

## 4. The C you can use

Leap-C compiles a **subset of C89** (ANSI C), roughly Small-C plus `unsigned`, `struct`, `enum`, `typedef`, function pointers, multi-dimensional arrays and `float`. Anything outside it is a compile error, `ERROR 1: NOT SUPPORTED`, never a silent miscompilation.

**Supported:**

- **Types:** `char` (8 bits, **unsigned**), `signed char`, `unsigned char`, `int` and `short` (16 bits), `unsigned` (16 bits), pointers (16 bits), arrays of any dimension, `struct` (no padding), `enum`, `typedef`, `void`, `float` and `double` (the same type: §6), pointers to functions, `const` (checked for assignment), `static`, `extern` (one file only), `register` and `auto` (ignored).
- **Expressions:** every C89 operator, with the usual conversions (`unsigned` wins over `int`), pointer arithmetic, casts, `sizeof`, `?:`, the comma operator, compound assignment, `++` and `--`, short-circuit `&&` and `||`. Constant expressions are folded at compile time.
- **Statements:** all of C89: `if`/`else`, `while`, `do`/`while`, `for`, `switch` (on integers and `char`), `break`, `continue`, `goto` and labels, `return`, blocks with declarations at their start.
- **Functions:** ANSI definitions, prototypes (optional: a function can be called before it is defined), recursion, up to 16 parameters, pointers to functions. `int main(void)` or `void main(void)`; `main`'s return value is the `EXIT` report.
- **Initialisers:** for global and `static` variables, all of C89's (arrays, structs, nested braces, strings, addresses); for local variables, scalars only.
- **Preprocessor:** `#define NAME text` and `#undef NAME`; `#include <leap.h>` (ignored); `#pragma hires` (§7).
- **Comments:** `/* ... */` and `// ...`.

**Not supported** (`NOT SUPPORTED`): `long`, `union`, `volatile`, `long double`; struct parameters, struct return values and struct assignment (use pointers and `memcpy`); initialisers on local arrays and structs (declare them `static`, or assign the elements); your own variadic (`...`) functions; old-style (K&R) function definitions; function-like macros (`#define f(x)`), `#if`, `#ifdef` and the other directives; `#include` of any other file; several source files.

**Differences from standard C to watch for:**

| | Leap-C |
|---|---|
| `int` | 16 bits: -32768 to 32767; overflow wraps around |
| `char` | unsigned: `char c = 255;` stays 255 |
| division by zero (integer) | gives 0 (remainder 0); no error |
| `float` and `double` | one type, the Sinclair 5-byte format: about 9.6 digits, up to 1.7E38; not IEEE (§6) |
| a macro defined twice | `ALREADY DEFINED`, even with the same text (C allows identical redefinition): `#undef` it first |
| declaring a library function yourself | your prototype of, say, `strlen` declares a new function that you must then define; leave library functions undeclared |
| `printf` | `%d %u %x %c %s %%`, `%f` and `%.Nf`, a width; no flags (`- 0 + #`), no `%e`/`%g`; its return value is undefined |
| no checks | array bounds and NULL pointers are not checked: this is C |

## 5. The built-in library

All of these need no declaration. Text rows are 0-23 and columns 0-31; pixels are x 0-255, y 0-191, counted **from the top left**. A "frame" is a 60th of a second on a TS2068 (a 50th on ZEsarUX: [EMULATORS.md](EMULATORS.md) §8).

| Function | Does |
|---|---|
| **Text** | |
| `cls()` | clears the screen to the current colours; printing starts at the top left |
| `putchar(c)` | prints a character; returns it |
| `puts(s)` | prints a string and a new line |
| `print(s)` | prints a string, no new line |
| `printf(fmt, ...)` | formatted printing: `%d %u %x %c %s %%`, `%f`, `%.Nf` (N 0-9), a width (`%5d`) |
| `at(row, col)` | moves the print position |
| `tab(col)` | moves to a column on the current row |
| `ink(n)`, `paper(n)` | colours 0-7 (black, blue, red, magenta, green, cyan, yellow, white) |
| `border(n)` | the border's colour |
| `bright(n)`, `flash(n)`, `inverse(n)`, `over(n)` | 0 or 1; `over(1)` prints and plots by exclusive-or |
| **Keyboard** | |
| `getkey()` | waits for a key and returns it (ASCII; 8 DELETE, 13 ENTER, 1-4 the cursor keys) |
| `inkey()` | the key pressed since the last call, or 0 |
| `gets(buf, max)` | reads a line of at most `max - 1` characters, with DELETE; returns `buf` |
| **Graphics** | |
| `plot(x, y)` | sets a pixel |
| `draw(x0, y0, x1, y1)` | draws a line, both ends included |
| `point(x, y)` | 1 if the pixel is set, else 0 |
| `attr(row, col)` | a character cell's attribute byte |
| `mode(n)` | 0: normal; 1: the TS2068's high-resolution colour mode (§7) |
| `sprite_get(row, col, w, h, buf)`, `sprite_put(...)` | copy a rectangle of character cells to and from memory (9 bytes a cell) |
| **Sound** | |
| `beep(frames, semitone)` | plays a note for that many frames; semitone 0 is middle C (-60 to 69) |
| `sound(reg, value)` | writes a register (0-15) of the AY sound chip |
| **Time and random numbers** | |
| `frames()` | a counter of frames (`unsigned`) |
| `pause(n)` | waits n frames |
| `rand()`, `srand(n)` | pseudo-random numbers 0-32767; `srand` restarts the sequence |
| **Strings and memory** | |
| `strlen`, `strcpy`, `strncpy`, `strcmp`, `strcat`, `strchr` | as in C |
| `memcpy`, `memmove`, `memset`, `memcmp` | as in C (`memcpy` copes with overlap) |
| **Conversion** | |
| `atoi(s)`, `itoa(n, buf, base)`, `abs(n)` | text to `int`; `int` to text in bases 2-36; absolute value |
| **Memory and ports** | |
| `malloc(n)`, `free(p)` | the heap; `malloc` returns NULL when nothing fits |
| `inp(port)`, `outp(port, value)` | read and write the Z80's I/O ports |
| **Program** | |
| `exit(n)` | ends the program from anywhere, with `EXIT n` |
| **Tape** (§8) | |
| `tape_save(name, addr, len)` | saves `len` bytes from `addr` as a data tape |
| `tape_load(name, addr, max)` | loads a data tape (`""`: any); returns its length, or a negative number on failure |

A wrong argument where it is checked (`beep()`'s semitone, `sound()`'s register, `mode()`, `itoa()`'s base, a sprite off the screen, a tape name longer than 10 characters) stops the program with runtime error 4 (§10).

## 6. Floating point

`float` and `double` are the same type: the TS2068 ROM's own 5-byte number format, with about 9.6 significant digits and magnitudes up to about 1.7E38. Integers convert to `float` exactly; a `float` converts to an integer by dropping the fraction. `printf("%f")` prints 6 decimals, `%.2f` two; every digit before the point is printed. There is no maths library (`sqrt`, `sin`, ...) and no `%e`; such functions are short to write in C ([EXAMPLES.md](EXAMPLES.md) §8 has `sqrt`).

```c
// expect: exit 3
// screen: 0 AREA 78.54
// screen: 1 1.50 0.333
int main(void)
{
    float r = 5.0;
    float area = 3.14159265 * r * r;
    cls();
    printf("AREA %.2f\n", area);
    printf("%.2f %.3f\n", 3 / 2.0, 1.0 / 3);
    return (int)(10.0 / 3);
}
```

A float overflow or a division of a float by zero stops the program with runtime error 6 (`NUMBER TOO BIG`). Float arithmetic is much slower than integer arithmetic (a multiplication takes about 20,000 T-states, some 6 ms): use integers where you can.

## 7. Graphics, sound and the keyboard

```c
// expect: exit 1
// pixel: 0 0 1
// pixel: 255 191 1
// attr: 0 0 0x3A
int main(void)
{
    cls();
    ink(2);
    draw(0, 0, 255, 191);
    plot(128, 20);
    beep(10, 12);
    return point(128, 20);
}
```

This draws a red diagonal across the screen, sets a pixel near the top, and plays the C an octave above middle C for 10 frames.

Reading keys: `getkey()` waits, `inkey()` only looks. This program counts until a key is pressed:

```c
// keys: "q"
// expect: exit 113
int main(void)
{
    int n = 0, k;
    cls();
    while ((k = inkey()) == 0) {
        at(0, 0);
        printf("%d   ", n++);
        pause(1);
    }
    return k;
}
```

It returns the key's code (`'q'` is 113). **BREAK** (CAPS SHIFT + SPACE) stops any program: the report is `BREAK` and `LINE m`.

**High resolution.** `mode(1)` switches the TS2068 to its high-resolution colour mode, which uses the memory at `$6000-$77FF`. The compiler fills that memory last, so only a large program reaches it; `#pragma hires` keeps the compiled program out of it, and a program that uses `mode(1)` should say so. If the program is there, `mode(1)` stops with runtime error 3. The end of a program restores mode 0.

## 8. Tapes

[EMULATORS.md](EMULATORS.md) §7 says how to work a tape in each emulator.

- **Programs:** `SAVE "name"` writes your program (its source) to tape; `LOAD "name"` or `LOAD ""` reads one back, replacing the program in the editor; `VERIFY "name"` checks a tape. `tools/c2tape.py` (in the repository: [EMULATORS.md](EMULATORS.md) §7.4) makes a tape from a `.c` file on a PC.
- **Data:** a program can save and load its own data with `tape_save(name, addr, len)` and `tape_load(name, addr, max)`. `tape_load` returns the length loaded, or -1 when nothing was loaded (no such tape within about 2 minutes, or a tape longer than `max`), -2 when the data failed after part of it arrived, -3 for a tape that is not Leap-C's. A program's tape and a data tape are different kinds: `LOAD` skips data tapes and `tape_load` skips programs.
- **BREAK** or SPACE stops a tape command (report `BREAK`), and stops `tape_save` and `tape_load` with runtime error 5.

Leap-C's tapes carry their own version word, so the TS2068's BASIC and Leap V2 refuse them, and Leap-C refuses theirs (`BAD TAPE VERSION`). While a tape block moves, `frames()` does not count.

## 9. Loading a library

A library adds functions written in assembly. The beta comes with one, **shapes**: on the empty last line type `LIB "shapes"` and play `shapes.tzx` (or `.tap`). The report is `LIBRARY shapes: 3 FUNCTIONS`, and three functions are then available, called like the built-in ones without a declaration:

| Function | Does |
|---|---|
| `circle(x, y, r)` | draws a circle of radius r (with `over(1)`, a second call erases it) |
| `box(x0, y0, x1, y1)` | draws a rectangle's four sides |
| `isqrt(n)` | the integer square root of an `unsigned` n (the result is 0-255) |

```c
// library: shapes
// expect: exit 7
// screen: 0 ROOT 12
// pixel: 158 96 1
int main(void)
{
    cls();
    printf("ROOT %u", isqrt(150));
    circle(128, 96, 30);
    box(60, 40, 196, 152);
    return isqrt(64) - 1;
}
```

One library is loaded at a time; `LIB "other"` replaces it. It stays through `NEW`, `LOAD` and `RUN`; `LIB` alone unloads it, and a reset clears it. While a library is loaded it occupies image region 3 (1 KB), so the largest program is 1 KB smaller. Without the library, a call to `circle` is `ERROR 70: UNDEFINED FUNCTION`. You can write your own libraries in assembly: `include/leapc_lib.inc` and `tools/lib2tape.py` in the repository.

## 10. Error reports

**Compile errors.** The compile stops at the first error. The report is `ERROR n: MESSAGE` and `LINE m`; for an undeclared, undefined or duplicated name, the name too (`LINE 5  'cont'`). Press a key: the editor shows line m with the cursor **at the place where the compiler stopped** (for a missing `;`, at the end of the line that lacks it). For example, this program:

```c
// expect: error E_UNDECL 5
int main(void)
{
    int count = 0;
    return cont;
}
```

reports `ERROR 23: UNDECLARED IDENTIFIER`, `LINE 5  'cont'`, with the cursor just after `cont`. Line numbers count from 1, the program's first line (here the `// expect` comment; typed without it, the same error is on line 4).

| Group | Numbers and messages |
|---|---|
| not supported | 1 NOT SUPPORTED |
| characters and numbers | 10 BAD CHARACTER, 11 UNTERMINATED COMMENT, 12 UNTERMINATED STRING, 13 BAD CHARACTER CONSTANT, 14 BAD ESCAPE, 15 BAD NUMBER, 16 NUMBER TOO LARGE, 17 STRING TOO LONG |
| declarations | 20 SYNTAX ERROR, 21 REDECLARED, 22 ALREADY DEFINED, 23 UNDECLARED IDENTIFIER, 24 BAD TYPE SPECIFIERS, 25 BAD DECLARATOR, 26 BAD STORAGE CLASS, 27 BAD PARAMETER, 28 BAD INITIALISER, 29 BAD ARRAY SIZE |
| types | 40 TYPE MISMATCH, 41 INCOMPLETE TYPE, 42 TYPE TOO LARGE |
| expressions | 50 CONSTANT REQUIRED, 51 BAD OPERAND TYPE, 52 NO SUCH MEMBER, 53 NOT AN LVALUE, 54 ASSIGNMENT TO CONST, 55 WRONG ARGUMENT COUNT |
| statements | 70 UNDEFINED FUNCTION, 71 NO MAIN FUNCTION, 72 MISPLACED BREAK, 73 MISPLACED CONTINUE, 74 MISPLACED CASE, 75 DUPLICATE CASE, 76 UNDEFINED LABEL |
| limits | 90 NESTING TOO DEEP, 91 FRAME TOO LARGE, 92 TOO MANY PARAMETERS |
| memory | 100 OUT OF MEMORY, 101 PROGRAM TOO BIG |

**Runtime errors.** The program stops with `RUNTIME ERROR n: MESSAGE` and `LINE m`, the line where the function that failed **starts** (its definition's first line). A key returns to the editor with the cursor there.

| Number | Message | Cause |
|---|---|---|
| 1 | STACK OVERFLOW | recursion too deep, or too many large locals |
| 3 | HI-RES IN USE | `mode(1)` while the compiled program occupies `$6000-$77FF` (a large program without `#pragma hires`) |
| 4 | BAD ARGUMENT | a checked library argument out of range (§5) |
| 5 | (shown as `BREAK`) | BREAK pressed, or SPACE during `tape_save`/`tape_load` |
| 6 | NUMBER TOO BIG | a float overflow or float division by zero |

## 11. Limits

| Item | Limit |
|---|---|
| program source | about 18 KB (`FREE` shows what is left); a typical program of 850 lines fits |
| compiled program | 19,840 B of code and data, in four regions; a single object at most 8 KB |
| line length | 127 characters; a string literal on one line, 126 characters |
| names | 31 significant characters |
| local variables | 255 bytes per function (use `static` or the heap for more) |
| function parameters | 16 |
| recursion | about 190 levels of a function with one `int` parameter and one local |
| heap | up to about 18 KB with a small program; less as the source grows |
| a library | 1 KB (image region 3) |
| compile speed | about 13 ms per line |

`FREE` reports the space left. `ERROR 100: OUT OF MEMORY` means the source and the compiler's tables no longer fit together: shorten the program. `ERROR 101: PROGRAM TOO BIG` means the compiled code and data do not fit.
