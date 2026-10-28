# Appendices

## Appendix A: Reports and messages

What the bottom two rows of the screen can say. A command or a run ends with a **report** on rows 22 and 23, in white on black, drawn over whatever is on the screen; it stays until a key is pressed. The key is not typed: it only dismisses the report. A key still held down from the command (the ENTER of `RUN`, BREAK) is let go of first, and a key pressed meanwhile, its auto-repeat included, is ignored, so a report cannot vanish before you can read it. Then the editor is redrawn with your program as it was.

The commands are described in [Part 3](03_keywords.md) and the errors in [Part 5](05_concepts.md#errors).

### The status row of the editor

| Message | Meaning |
|---|---|
| `LINE n/m` | not an error: the cursor is on line *n* of a program of *m* lines (row 23, white on black, with a red, green and blue swatch at the right). After switching on it is `LINE 1/0` |
| `PROGRAM FULL` | the line you just entered does not fit in the memory for the source; it was not stored and stays in the edit buffer |
| `COMPILING` | `RUN` is compiling |
| `SAVING name` | a tape is being written |
| `LOADING`, `LOADING name` | a tape (a program for `LOAD`, a library for `LIB`) is being searched for; then its header was found, with its name. `VERIFYING` and `VERIFYING name` likewise |
| `NO LIBRARY` | `LIB` alone unloaded the library |

### The report of RUN

| Row 22 | Row 23 | Meaning |
|---|---|---|
| `EXIT n` | `IMAGE i B  HEAP h B` | the program ended. *n* is what `main` returned, or the argument of `exit()` (signed; 0 for a `void main`). *i* is the size of the compiled program in bytes, *h* the largest block `malloc()` could have returned |
| `ERROR n: MESSAGE` | `LINE m` | the compile stopped at the first error; the messages are in [Appendix B](#appendix-b-compile-error-codes). For errors 21, 22, 23, 52, 70 and 76 row 23 also gives the name: `LINE 5  'cont'` (at most 15 characters). When you press a key the editor shows line *m* with the cursor at the place where the compiler stopped (after a missing `;`, at the end of the line) |
| `RUNTIME ERROR n: MESSAGE` | `LINE m` | the program stopped; the messages are in [Appendix C](#appendix-c-runtime-errors). *m* is the line where the function that failed starts; the row has no `LINE` when that is unknown |
| `BREAK` | `LINE m` | you pressed BREAK (CAPS SHIFT + SPACE), or SPACE during `tape_save` or `tape_load` |

The program's own screen stays above (rows 0 to 21) while the report is up. A program starts with the screen as the editor left it, so call `cls()` before printing. Compile speed is about 13 ms per line: a longer program shows `COMPILING` a little longer.

### The reports of the other commands

Row 23 of every tape command's report, whatever the outcome, is `SOURCE s B  FREE f B`.

| Command | Row 22 | Meaning |
|---|---|---|
| `FREE` | `SOURCE s B  FREE f B` and `IMAGE i B  HEAP h B` | *s* is the size of the program in the line store, *f* the room left for it, *i* the size of the last compiled program (0 before any), *h* the heap a program would have with the source as it is |
| `LIST` | (the listing) | the program a page (23 rows) at a time with keywords in bold; a key shows the next page; BREAK ends the listing |
| `SAVE "name"` | `SAVED name` | the program is on tape |
| | `BREAK` | SPACE stopped it; no data block was written |
| | `BAD NAME` | the name is longer than 10 characters, has no closing quote, or something follows the closing quote |
| | `NO PROGRAM` | the program is empty: nothing to save |
| `LOAD "name"`, `LOAD ""` | `LOADED name` | the program on the tape replaced the one in the editor; the cursor is on the empty last line |
| | `LOAD FAILED` | no such tape before the search gave up (about two minutes), a tape that is too long for the memory, or a damaged tape; your program is kept (see below) |
| | `BAD TAPE VERSION` | not a Leap-C program tape: a TS2068 BASIC tape, a Leap V2 tape, a library, or a later Leap-C format. Refused before anything is written |
| | `BREAK` | SPACE stopped it |
| | `BAD NAME` | as for `SAVE` (but `""` is allowed: the next program tape) |
| `VERIFY "name"`, `VERIFY ""` | `VERIFIED name` | the tape holds exactly the program in the editor and ends where it does. Nothing is written |
| | `VERIFY FAILED` | the tape and the program differ, or the tape does not end where the program does |
| | `BAD TAPE VERSION`, `BREAK`, `BAD NAME` | as for `LOAD` |
| `LIB "name"`, `LIB ""` | `LIBRARY name: n FUNCTIONS` | see [Part 6](06_libraries.md#loading-a-library) |
| | `BAD TAPE VERSION`, `LOAD FAILED`, `BREAK`, `BAD NAME` | as there |
| `LIB` | `NO LIBRARY` | the library was unloaded |

A failed `LOAD` leaves your program and the editor as they were, except when the tape's program did not fit above the program in memory and part of it had already arrived: then the program is empty, as after `NEW`. That includes BREAK pressed once part of such a program has arrived.

A command is recognised only on the empty last line, alone on the line apart from spaces, in capitals or small letters; anything else typed there is a new line of the program. The tape commands are the word, spaces and a quote, so `save(x);` is C source and `SAVE` alone is also source.

---

## Appendix B: Compile error codes

The report shows `ERROR n: MESSAGE` and `LINE m`. The compile **stops at the first error**; nothing ran. Numbers are grouped by tens: 1 not supported, 10-19 characters and numbers, 20-29 declarations, 40-49 types, 50-59 expressions, 70-79 statements and functions, 90-99 limits, 100-109 memory. Line numbers count from 1 at the program's first line; an error is at the line of the token where it was found, and for a missing token (`;`, `)`, `]`, `}`, `:`) at the line of the token before it, after which the missing one belongs.

| Code | Message | Cause |
|---:|---|---|
| 1 | `NOT SUPPORTED` | something outside the subset: `long`, `union`, `volatile`, `long double`, bit-fields, struct parameters, struct return values or struct assignment, an initialiser on a local array or struct, your own variadic functions, old-style (K&R) definitions, function-like macros, `#if` and the other directives, `#include` of any other file, `#pragma` other than `hires`, several source files (see [Differences from standard C](05_concepts.md#differences-from-standard-c)) |
| 10 | `BAD CHARACTER` | a character outside ASCII 32 to 126, or one that is not a C token: `@`, `$`, `` ` ``, and a stray `\` |
| 11 | `UNTERMINATED COMMENT` | a `/*` that is never closed; reported at the line where it starts |
| 12 | `UNTERMINATED STRING` | the end of the line inside a `"..."` |
| 13 | `BAD CHARACTER CONSTANT` | `''`, an unterminated constant, or more than one character in it |
| 14 | `BAD ESCAPE` | a backslash sequence that is not known; `\x` without digits; a value above 255 |
| 15 | `BAD NUMBER` | an invalid digit or suffix; `0x` without digits; a malformed floating constant (`1e`) |
| 16 | `NUMBER TOO LARGE` | an integer constant above 65535, or a floating constant, or a constant floating expression, beyond the range of `float` |
| 17 | `STRING TOO LONG` | a string literal longer than the editor can make (a safeguard that no typed line reaches) |
| 20 | `SYNTAX ERROR` | a token that cannot appear here: a missing `;`, `)` or `}`, a stray token, a braced initialiser of two values for a scalar |
| 21 | `REDECLARED` | the name is already declared differently in this scope (row 23 shows the name) |
| 22 | `ALREADY DEFINED` | a second body, initialiser or `struct`/`enum` definition; also a macro defined twice, even with the same text (use `#undef` first) |
| 23 | `UNDECLARED IDENTIFIER` | a name that was never declared (row 23 shows it) |
| 24 | `BAD TYPE SPECIFIERS` | a combination that is not a type: `int char`, `signed unsigned`, `short short`, `int T` |
| 25 | `BAD DECLARATOR` | an array of functions, a function returning an array or a function, a `void` parameter or member, a function definition where one cannot be |
| 26 | `BAD STORAGE CLASS` | two storage classes, `auto` at file scope, `typedef` with an initialiser |
| 27 | `BAD PARAMETER` | a parameter without a name in a function definition |
| 28 | `BAD INITIALISER` | too many elements, a string too long for its array, braces missing for an aggregate |
| 29 | `BAD ARRAY SIZE` | an array of zero or negative size |
| 40 | `TYPE MISMATCH` | conflicting declarations; an incompatible initialiser or argument (an integer for a pointer, a pointer for an `int` parameter of a library function) |
| 41 | `INCOMPLETE TYPE` | a `void` object, a `struct` that is not defined, `[]` without a size |
| 42 | `TYPE TOO LARGE` | an object of more than 65535 bytes |
| 50 | `CONSTANT REQUIRED` | a constant expression is needed here (a `case`, an array size, an initialiser of a global) |
| 51 | `BAD OPERAND TYPE` | an operator on a type it does not take: `*` of an `int`, `.` of a non-struct, two pointers added |
| 52 | `NO SUCH MEMBER` | the `struct` has no member of that name (row 23 shows it) |
| 53 | `NOT AN LVALUE` | `&` of a value, or an assignment to something that is not a variable |
| 54 | `ASSIGNMENT TO CONST` | a `const` object assigned or incremented |
| 55 | `WRONG ARGUMENT COUNT` | a call of a function with a prototype (a library function included) with too few or too many arguments |
| 70 | `UNDEFINED FUNCTION` | a function called or used but never defined; the line is that of its first use, and row 23 shows the name. A library function without its library gives this |
| 71 | `NO MAIN FUNCTION` | `RUN` with no `main`; reported at the last line |
| 72 | `MISPLACED BREAK` | `break` outside a loop or `switch` |
| 73 | `MISPLACED CONTINUE` | `continue` outside a loop |
| 74 | `MISPLACED CASE` | `case` or `default` outside a `switch` |
| 75 | `DUPLICATE CASE` | a `case` value twice (also `case A: case 'A':` when both are 65), or a second `default` |
| 76 | `UNDEFINED LABEL` | a `goto` to a label that the function does not define; the line of the first such `goto`; row 23 shows the name |
| 90 | `NESTING TOO DEEP` | the compiler's stack guard: more than 15 `*` in a declarator; macros nested more than 8 deep or one expansion of more than 255 tokens; too many nested brackets, blocks or calls; more than 32 argument words pending |
| 91 | `FRAME TOO LARGE` | more than 255 bytes of local variables in a function (use `static` or the heap) |
| 92 | `TOO MANY PARAMETERS` | more than 16 parameters |
| 100 | `OUT OF MEMORY` | the source and the compiler's tables no longer fit together: shorten the program |
| 101 | `PROGRAM TOO BIG` | the compiled code and data do not fit the four image regions |

Codes that are not in the table (2 to 9, 18, 19, 30 to 39, 43 to 49, 56 to 69, 77 to 89, 93 to 99 and 102 upward) are not used. Some programs that each cause an error, with the line the report gives (the line numbers count the `// expect:` comment as line 1):

```c
// expect: error E_UNDECL 5
int main(void)
{
    int count = 0;
    return cont;
}
```

```c
// expect: error E_SYNTAX 5
int x;
int main(void)
{
    x = 1
    return x;
}
```

(Error 20, a missing `;`, is reported at the line of the statement that lacks it, here line 5, and the cursor goes to the end of that line.)

```c
// expect: error E_CONST 5
const int c = 1;
int main(void)
{
    c = 2;
    return 0;
}
```

```c
// expect: error E_ARGS 5
int f(int a, int b) { return a + b; }
int main(void)
{
    return f(1);
}
```

```c
// expect: error E_BREAK 5
int main(void)
{
    int x;
    break;
    return 0;
}
```

```c
// expect: error E_UNDEFLABEL 3
int f(void) { lab: return 1; }
int main(void) { goto lab; return 0; }
```

```c
// expect: error E_RANGE 2
int big = 65536;
```

```c
int f(void) { return 1; }
int x;
```

`NO MAIN FUNCTION` is reported at the program's last line: here `LINE 2`. (This one example is not an automated test: the test harness adds a line to the end of every example, which moves the last line.)

---

## Appendix C: Runtime errors

The program stopped. The report is `RUNTIME ERROR n: MESSAGE` and `LINE m`; *m* is the line where the **function that failed starts** (its definition's first line). For an error raised by a library function (built-in or loaded) it is the function that **called** the library. A key returns to the editor with the cursor there. Where the part of a function that continues in the memory at `$6000` fails, the line is unknown and `LINE` is left out.

| Code | Message | Cause |
|---:|---|---|
| 1 | `STACK OVERFLOW` | recursion too deep, or too many large locals: a function was entered with its frame below `$F900`. Reported at the function being entered |
| 2 | `OUT OF HEAP` | not raised by any library function of this release: `malloc` returns NULL instead |
| 3 | `HI-RES IN USE` | `mode(1)` while the compiled program occupies `$6000-$77FF` (a large program without `#pragma hires`) |
| 4 | `BAD ARGUMENT` | a checked argument out of range: `beep()` with a semitone outside -60 to 69; `sound()` with a register above 15; `mode()` with another number than 0 or 1; `itoa()` with a base outside 2 to 36; `sprite_get()` or `sprite_put()` with a rectangle that is empty or not wholly on the screen; `tape_save()` or `tape_load()` with a name longer than 10 characters (and `tape_save()` with an empty name or a length of 0); a negative radius for `circle()` of the shapes library; a call of a reserved library slot |
| 5 | (shown as `BREAK`) | BREAK pressed (CAPS SHIFT + SPACE), or SPACE during `tape_save` or `tape_load` |
| 6 | `NUMBER TOO BIG` | a `float` overflow, or a division of a `float` by zero |

Integer division by zero is **not** an error: it gives 0 (and the remainder is 0).

Programs that stop with each error (the `// rtline:` line states the line the report gives; the line numbers count the comments):

```c
// expect: rterror 4
// rtline: 3
int main(void)
{
    beep(1, 99);
    return 0;
}
```

```c
// expect: rterror 4
char data[4];
int main(void)
{
    tape_save("a_long_file_name", data, sizeof data);
    return 0;
}
```

```c
// expect: rterror 6
int main(void)
{
    float zero = 0;
    return 1 / zero;
}
```

In a constant expression the same overflow is a compile error (`NUMBER TOO LARGE`, 16). Runaway recursion stops with error 1 instead of overwriting memory:

```c
// expect: rterror 1
// noaudit
int down(int n)
{
    return down(n + 1) + 1;
}
int main(void)
{
    return down(0);
}
```

(The line `// noaudit` is an instruction to the test harness: it tells it not to check every return of the function, of which there are none.) Array bounds and NULL pointers are not checked: this is C.

---

## Appendix D: Character set and keyboard

### The character set

`char` is **unsigned** (0 to 255). The characters Leap-C prints are:

| Codes | Characters |
|---|---|
| 32 to 126 | all of printable ASCII, each with a picture. A character outside them in a program is error 10 (`BAD CHARACTER`) |
| 128 to 143 | 16 **block graphics**, 2 x 2 blocks of 4 x 4 pixels |
| 144 to 164 | 21 **user-defined characters**, eight bytes each from `$F180` (the first is code 144). They are blank until a program writes them (example 13 in [Part 7](07_examples.md#13-a-character-of-your-own)); a cold start clears them |
| 0 to 31, 127, 165 to 255 | nothing is drawn: a blank |

The characters C needs and the TS2068 lacks were added: `[` `]` `{` `}` `|` `~` `^` `\`. Their pictures are drawn like the rest of the font: `\` is the mirror of `/`, `|` a solid bar and `{` `}` braces with a centre point. The zero has a slash, so that it differs from the letter O.

**Block graphics.** Each bit of (*code* - 128) is one quarter of the cell: bit 0 the top right, bit 1 the top left, bit 2 the bottom right, bit 3 the bottom left. This program prints each of the sixteen in a cell and reads four of its pixels back, one in each quarter (1 means filled), in the order top left, top right, bottom left, bottom right:

```c
// expect: exit 0
// screen: 0 128 0000
// screen: 1 129 0100
// screen: 2 130 1000
// screen: 3 131 1100
// screen: 4 132 0001
// screen: 5 133 0101
// screen: 6 134 1001
// screen: 7 135 1101
// screen: 8 136 0010
// screen: 9 137 0110
// screen: 10 138 1010
// screen: 11 139 1110
// screen: 12 140 0011
// screen: 13 141 0111
// screen: 14 142 1011
// screen: 15 143 1111
char t[16][5];
int main(void)
{
    int c, i;
    for (c = 128; c < 144; c++) {
        cls();
        putchar(c);
        i = c - 128;
        t[i][0] = '0' + point(0, 0);
        t[i][1] = '0' + point(7, 0);
        t[i][2] = '0' + point(0, 7);
        t[i][3] = '0' + point(7, 7);
    }
    cls();
    for (i = 0; i < 16; i++)
        printf("%d %s\n", 128 + i, t[i]);
    return 0;
}
```

```text
128 0000
129 0100
130 1000
131 1100
132 0001
133 0101
134 1001
135 1101
136 0010
137 0110
138 1010
139 1110
140 0011
141 0111
142 1011
143 1111
```

### The keyboard

Letters, digits and SPACE type themselves; CAPS SHIFT + a letter gives a capital. SYMBOL SHIFT + a key gives the punctuation of the table. The first eight are Leap-C's own, because C needs them and the TS2068's keys do not give them; the rest are the TS2068's.

| SYMBOL SHIFT + | Y | U | F | G | S | A | H | D |
|---|---|---|---|---|---|---|---|---|
| gives | `[` | `]` | `{` | `}` | `\|` | `~` | `^` | `\` |

| SYMBOL SHIFT + | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| gives | `!` | `@` | `#` | `$` | `%` | `&` | `'` | `(` | `)` | `_` |

| SYMBOL SHIFT + | P | O | Z | R | T | C | L | K | J | B | V | N | M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gives | `"` | `;` | `:` | `<` | `>` | `?` | `=` | `+` | `-` | `*` | `/` | `,` | `.` |

The editing keys:

| Keys | Does | Code |
|---|---|---|
| ENTER | store the line and go to the next | 13 |
| CAPS SHIFT + 5 / 6 / 7 / 8 | cursor left / down / up / right (between the rows of a wrapped line first) | 1 / 2 / 3 / 4 |
| CAPS SHIFT + 0 (DELETE) | delete the character before the cursor; on an empty line, delete the line | 8 |
| CAPS SHIFT + 1 | delete the whole line | |
| CAPS SHIFT + ENTER | insert an empty line before this one | |
| BREAK (CAPS SHIFT + SPACE) | stop a running program, a listing or a tape command | |

Moving off a line with the up or down key also stores it. Two letter keys pressed at the same moment type nothing. A held key repeats after about 0.6 s (35 frames), then every 5 frames. BREAK does nothing in the editor. Keywords turn **bold** when you leave a line (not identifiers that contain one, nor the text of strings, character constants and comments).

### What getkey() returns

`getkey()` and `inkey()` return the ASCII code of the key, or one of the editor's control codes:

| Code | Key |
|---:|---|
| 32 to 126 | the character typed |
| 1 | cursor left (CAPS SHIFT + 5) |
| 2 | cursor down (CAPS SHIFT + 6) |
| 3 | cursor up (CAPS SHIFT + 7) |
| 4 | cursor right (CAPS SHIFT + 8) |
| 8 | DELETE (CAPS SHIFT + 0) |
| 13 | ENTER |

`inkey()` returns 0 when no key has been pressed since the last call. The hardware kit's program H2 (`docs/hardware/keys.c`) prints each key's character and code, which is the way to find out what a key gives on your machine.

---

## Appendix E: Limits

Most of these are limits of **memory** and move with what else the program uses. Measured on the release (`make capacity`) with an otherwise empty program unless said otherwise.

| What | Limit |
|---|---|
| program source | about 18 KB: 18,412 bytes of line store for a program of comments and `main`; a typical program of 851 lines (15,087 bytes) fits. `FREE` shows what is left |
| compiled program | 19,840 bytes of code and data, in four regions; a single object at most 8,192 bytes (region 1) |
| characters in a program line | 127 |
| a string literal | one line, 126 characters (adjacent literals are joined) |
| significant characters in a name | 31 |
| function parameters | 16 |
| local variables of one function | 255 bytes (a `float` local takes 5); use `static` or the heap for more |
| argument words pending at one time | 32 (a `float` argument counts 3) |
| recursion | about 190 levels of a function with one `int` parameter and one local; 381 with no parameter and no local; 47 with four parameters and ten locals |
| nested parentheses | 112 |
| nested held operands or calls | 60 |
| nested blocks | 154 |
| nested `if` | 386 |
| nested `while` | 193 |
| macro expansions nested in one another | 8; tokens produced by one macro expansion: 255 |
| levels of `*` in a declarator | 15 |
| `case` labels in a `switch` | memory-bound (6 bytes of compiler workspace each) |
| the heap | up to about 18 KB with a small program (18,316 bytes in the largest block of the smallest program); less as the program grows (234 bytes with 18,193 bytes of source). `malloc` returns NULL for 32 KB or more |
| `int` and `unsigned` | 16 bits: -32768 to 32767, 0 to 65535; overflow wraps |
| `float` and `double` | one type: 5 bytes, about 9.6 significant digits, magnitude up to about 1.7E38 |
| `printf` | `%f` prints 6 decimals, `%.Nf` N of them (0 to 9; more counts as 9); every integer digit is printed (up to 39) |
| `rand()` | 0 to 32767 |
| text screen | 32 columns by 24 rows (0 to 23); in the editor row 23 is the status row |
| graphics screen | 256 by 192 pixels from the top left |
| `beep` | semitone -60 to 69 (below -39 plays the lowest note, A0); frames 0 to 65535 |
| `sound` | AY registers 0 to 15 |
| colours | `ink`, `paper`: 0 to 7 (only the low three bits are used); `bright`, `flash`, `inverse`, `over`: 0 or 1 (the low bit) |
| tape name | 1 to 10 characters (0 to 10 for `LOAD`, `VERIFY` and `LIB`: `""` is any) |
| a library | 1,024 bytes (region 3), 1 to 99 functions |
| tape search | about two minutes without a tape, then `LOAD FAILED` (or -1 from `tape_load`) |
| compile speed | about 13 ms per source line |

A program that needs more than a limit stops with `NESTING TOO DEEP`, `OUT OF MEMORY`, `PROGRAM TOO BIG` or a runtime `STACK OVERFLOW`; see [Appendix B](#appendix-b-compile-error-codes) and [Appendix C](#appendix-c-runtime-errors).

---

## Appendix F: Memory map

For programs that use pointers into memory (such as `(char *)0xF180`), `memcpy`, `inp` and `outp`, and for the curious. Addresses are in hexadecimal. **Nothing in this appendix has been checked on a physical TS2068** (see [Appendix G](#appendix-g-hardware-notes)).

| Addresses | Bytes | Contents |
|---|---:|---|
| `$0000-$3FFF` | 16 KB | the HOME ROM (the last 48 bytes, `$3FD0-$3FFF`, are the library jump table) |
| `$4000-$57FF` | 6,144 | the display: pixels |
| `$5800-$5AFF` | 768 | the display: colour attributes (one per 8 x 8 cell) |
| `$5B00-$5D59` | 602 | the system variables |
| `$5D5A-$5FFF` | 678 | Leap-C's own cells (the shell and editor state, the compiler's state, the 264-byte source chunk window, the runtime cells; `F_ACC` `$5ED6`, `LIB_COL`/`LIB_ROW` `$5EC2`/`$5EC3` and `LIB_ATTR` `$5EC8` among them); 171 bytes of the range are free |
| `$6000-$77FF` | 6,144 | the second display file, used by `mode(1)` (high resolution); **or**, for a program too large for the other regions, image region 4 |
| `$7800-$BFFF` | 18,432 | the **source store** (line records, upward from `$7800`); while compiling, the compiler's workspace grows down from the top of this range; at run time, from the end of the source up to `$BFFE`, the **heap** |
| `$C000-$DFFF` | 8,192 | **image region 1**: the compiled program (code up from `$C000`, static data down from `$DFFF`). This is the RAM that the EXROM is paged over: a program runs with the EXROM paged out, so the RAM is visible to it; the editor and the compiler, which are in the EXROM, never write to it |
| `$E000-$F17F` | 4,480 | image region 2 |
| `$F180-$F3FF` | 640 | platform cells: the user-defined characters (`UDG_TABLE`, `$F180`, 168 bytes: 8 bytes for each of codes 144 to 164), the edit line buffer (`$F228`, 128 bytes) and cells that Leap-C does not use |
| `$F400-$F7FF` | 1,024 | **image region 3**; while a library is loaded, **the library** |
| `$F800-$FEFF` | 1,792 | the machine stack (growing down from `$FF00`); C locals live here. A function is entered only with its frame above `$F900` |
| `$FF00-$FFFF` | 256 | unused by the ROM |

The compiled program fills the regions in the order 1, 2, 3, 4: code grows up from the start of a region and static data grows down from its end, and a function can continue from one region into the next. An object (a global, a `static` local, a string literal) never spans regions. While a library is loaded, region 3 is closed to the program; `#pragma hires` closes region 4. A program is `PROGRAM TOO BIG` when all regions are full.

Programs run with the EXROM paged out and with interrupts enabled (IM 1). The source is resident and visible to the editor; the compiled program is not saved to tape, only the source is.

---

## Appendix G: Hardware notes

Everything in this manual was verified on two **emulators**, on the ROMs of the release it describes (1.0.0-beta.2): **ZEsarUX 13.0**, the qualification emulator (with the EXROM patch), and **Fuse 1.9.1**, an independent emulator that emulates the TS2068's own 60 Hz frame. **Nothing was tried on a physical TS2068**, a real cassette recorder, a joystick or a DOCK/EXROM cartridge. The physical checks were recorded as an owner-accepted qualification deviation, not as passes. `docs/HARDWARE_CHECKLIST.md` lists the tests to run when a machine is available (power-on and boot, the keyboard, programs, BREAK, timing at 60 Hz, display contention, tape, a long soak), and `make kit` builds the EPROM images and the check programs and tapes. In particular:

* **Frame rate.** A frame, the unit of `frames()`, `pause(n)` and `beep(frames, ...)`, is 1/60 second on a TS2068. Fuse emulates that. **ZEsarUX runs its TS2068 at 50 frames a second**, like a British Spectrum, so there `pause(60)` lasts 1.2 seconds. Programs run at the same speed per instruction on both; only time counted in frames differs.
* **Contention.** The two emulators model the display's memory contention differently: code in image region 4 (`$6000-$77FF`, in the contended memory) ran 23% slower than in region 1 on Fuse's TS2068 model and 15% slower on ZEsarUX's. The real machine decides which holds.
* **Tape.** The tapes use the TS2068's standard tape signal with a Leap-C header; timing was exercised through the emulators' tape input and, for `SAVE`, through Fuse's recorder. Cassette levels, wow and flutter have not been tried. The block routines are new in 1.0.0-beta.2 and written clean-room from `docs/TAPE_SIGNAL_SPEC.md`. ZEsarUX 13.0 cannot save Leap-C's tapes to a file (its tape output works only through traps on the stock ROM's routines): `SAVE` completes but writes nothing; use Fuse.
* **Sound.** `beep` and `sound` use the AY chip; they were checked by reading its registers back, not by listening on a TS2068 (the start-up chime included).
* **The keyboard.** All 95 printable characters were typed on the emulators' keyboard matrices. Switch bounce, ghosting with three keys and the reliability of BREAK are for the hardware to settle.
* **The EXROM paging.** The SCLD's paging of the EXROM into chunk 6 (every float operation, `beep` and the tape functions page it in and out) is checked in ZEsarUX only.
* **Power-on RAM.** From eight power-on patterns (random, `$FF`, `$55AA`, ...) the boot is identical to a boot from zeroed RAM; a real DRAM's contents are not one of them.
* **The EPROMs.** The images for a 27128 (HOME) and a 2764 (EXROM) are in the kit; access times, ROM-replacement adapters and the programmer's checksum against `CHECKSUMS.txt` are untried. There is no DOCK-cartridge build for hardware.

A difference on the hardware is a finding: please report it with the steps and the screen (see `docs/BETA_TESTING.md`).

---

## Appendix H: Index

Keywords, directives and shell commands are in [Part 3](03_keywords.md); the built-in functions are in [Part 4](04_library.md); the functions of the shapes library are in [Part 6](06_libraries.md).

### Keywords, directives and commands

| Group | Entries |
|---|---|
| **Types** | [`char`](03_keywords.md#char), [`int`](03_keywords.md#int), [`short`](03_keywords.md#short), [`unsigned`](03_keywords.md#unsigned), [`signed`](03_keywords.md#signed), [`float`](03_keywords.md#float), [`double`](03_keywords.md#double), [`void`](03_keywords.md#void), [`struct`](03_keywords.md#struct), [`enum`](03_keywords.md#enum), [`typedef`](03_keywords.md#typedef) |
| **Qualifiers and storage** | [`const`](03_keywords.md#const), [`static`](03_keywords.md#static), [`extern`](03_keywords.md#extern), [`register`](03_keywords.md#register), [`auto`](03_keywords.md#auto) |
| **Statements** | [`if`](03_keywords.md#if), [`else`](03_keywords.md#else), [`while`](03_keywords.md#while), [`do`](03_keywords.md#do), [`for`](03_keywords.md#for), [`switch`](03_keywords.md#switch), [`case`](03_keywords.md#case), [`default`](03_keywords.md#default), [`break`](03_keywords.md#break), [`continue`](03_keywords.md#continue), [`goto`](03_keywords.md#goto), [`return`](03_keywords.md#return) |
| **Operators** | [`sizeof`](03_keywords.md#sizeof); the other operators are in [Part 3](03_keywords.md) |
| **Not supported** | `long`, `union`, `volatile`: see [Differences from standard C](05_concepts.md#differences-from-standard-c) |
| **Directives** | [`#define`](03_keywords.md#define), [`#undef`](03_keywords.md#undef), [`#include`](03_keywords.md#include), [`#pragma`](03_keywords.md#pragma) |
| **Commands** | [`RUN`](03_keywords.md#run), [`LIST`](03_keywords.md#list), [`FREE`](03_keywords.md#free), [`NEW`](03_keywords.md#new), [`SAVE`](03_keywords.md#save), [`LOAD`](03_keywords.md#load), [`VERIFY`](03_keywords.md#verify), [`LIB`](03_keywords.md#lib) |

### Built-in functions

| Group | Functions |
|---|---|
| **Text** | [`cls`](04_library.md#cls), [`putchar`](04_library.md#putchar), [`puts`](04_library.md#puts), [`print`](04_library.md#print), [`printf`](04_library.md#printf), [`at`](04_library.md#at), [`tab`](04_library.md#tab), [`ink`](04_library.md#ink), [`paper`](04_library.md#paper), [`border`](04_library.md#border), [`bright`](04_library.md#bright), [`flash`](04_library.md#flash), [`inverse`](04_library.md#inverse), [`over`](04_library.md#over) |
| **Keyboard** | [`getkey`](04_library.md#getkey), [`inkey`](04_library.md#inkey), [`gets`](04_library.md#gets) |
| **Graphics** | [`plot`](04_library.md#plot), [`draw`](04_library.md#draw), [`point`](04_library.md#point), [`attr`](04_library.md#attr), [`mode`](04_library.md#mode), [`sprite_get`](04_library.md#sprite_get), [`sprite_put`](04_library.md#sprite_put) |
| **Sound** | [`beep`](04_library.md#beep), [`sound`](04_library.md#sound) |
| **Time and random numbers** | [`frames`](04_library.md#frames), [`pause`](04_library.md#pause), [`rand`](04_library.md#rand), [`srand`](04_library.md#srand) |
| **Strings and memory** | [`strlen`](04_library.md#strlen), [`strcpy`](04_library.md#strcpy), [`strncpy`](04_library.md#strncpy), [`strcmp`](04_library.md#strcmp), [`strcat`](04_library.md#strcat), [`strchr`](04_library.md#strchr), [`memcpy`](04_library.md#memcpy), [`memmove`](04_library.md#memmove), [`memset`](04_library.md#memset), [`memcmp`](04_library.md#memcmp) |
| **Conversion** | [`atoi`](04_library.md#atoi), [`itoa`](04_library.md#itoa), [`abs`](04_library.md#abs) |
| **Memory and ports** | [`malloc`](04_library.md#malloc), [`free`](04_library.md#free), [`inp`](04_library.md#inp), [`outp`](04_library.md#outp) |
| **Program** | [`exit`](04_library.md#exit) |
| **Tape** | [`tape_save`](04_library.md#tape_save), [`tape_load`](04_library.md#tape_load) |
| **Library: shapes** | [`circle`](06_libraries.md#circle), [`box`](06_libraries.md#box), [`isqrt`](06_libraries.md#isqrt) |

### Topics

| Topic | Where |
|---|---|
| Errors, reports | [Errors](05_concepts.md#errors), [Appendix A](#appendix-a-reports-and-messages), [B](#appendix-b-compile-error-codes), [C](#appendix-c-runtime-errors) |
| Memory | [Memory](05_concepts.md#memory), [Appendix F](#appendix-f-memory-map) |
| Tapes | [Tapes](05_concepts.md#tapes), [Part 6](06_libraries.md#loading-a-library) |
| High resolution | [High resolution](05_concepts.md#high-resolution) |
| Floating point | [Floating point](05_concepts.md#floating-point) |
| The editor and its keys | [The editor](05_concepts.md#the-editor), [Appendix D](#appendix-d-character-set-and-keyboard) |
| How C here differs from standard C | [Differences from standard C](05_concepts.md#differences-from-standard-c) |
| Writing a library | [Writing your own library](06_libraries.md#writing-your-own-library) |
| Worked programs | [Part 7](07_examples.md) |

---

## Appendix I: How this manual was checked

* Every program in this manual in a `c` block that contains a `// expect:` line is a **test**. `tools/docexamples.py` copies each one to `tests/doc/<document>_<NN>.c` (a generated file that ends with the document and line it comes from), and the executable corpus compiles and runs it on the production ROM: directly, through the shell's `RUN`, and under the RAM canary (`tools/exectest.py`; `make test`). `make check` fails if `tests/doc/` falls out of step with the documents, so an edit to an example that is not regenerated is caught.
* The `//` lines at the top of an example are its checked results, and ordinary comments to the compiler. `// expect: exit N` is the value `main` returns (the `EXIT n` report); `// expect: error E_NAME L` is the compile error and its line; `// expect: rterror N` is the runtime error, and `// rtline: L` the line the report gives; `// screen: ROW TEXT` is the text of a screen row (0 is the top); `// pixel: X Y V`, `// attr: ROW COL V` and `// ay: REG=V` are a pixel (from the top left), a cell's attribute and a sound chip register; `// keys: ...` are the keys typed while the program reads the keyboard (a number, `"text"`, `ENTER`, `DELETE`); `// library: shapes` loads the library first, as `LIB "shapes"` does. `// noaudit` tells the harness not to check every function return (for runaway recursion). The full list is at the top of `tools/exectest.py`.
* The program of [Part 7](07_examples.md), example 18, needs a tape and has no `// expect:` line: it is **not** a test. Blocks without an expectation (the assembly and tape fragments of [Part 6](06_libraries.md), the pictures made of text) are not tests either.
* The facts that are not examples come from the specification (`spec.md`), the error table (`include/leapc_errors.inc`), the library interface (`include/leapc_lib.inc`, `libs/shapes.asm`, `tools/lib2tape.py`), the user guide, the hardware checklist and the emulator guide, whose programs are themselves tests; where a fact is the design's and has not been seen on a machine, [Appendix G](#appendix-g-hardware-notes) says so.
* Nothing in this manual has been tried on a physical TS2068.
