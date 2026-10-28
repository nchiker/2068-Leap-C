# Part 5 -- Concepts

The ideas behind the language and the machine, in alphabetical order. Where a keyword, an operator or a library function is the natural place to start, the entry points to it in [Part 3](03_keywords.md) or [Part 4](04_library.md).

Every program in this part that carries `// expect:` lines is a test: the build runs it on the ROM and checks the results the `//` lines state. To the compiler those lines are ordinary comments, so you can type the programs with or without them. (A line number in an `expect: error` line counts from the first line of the program, the `//` lines included; typed without them, the numbers drop.)

---

## Arrays

An array is a numbered row of values of one type, with one name: `a[0]`, `a[1]`, `a[2]`, ... You declare it with its size in square brackets.

* The first element is number **0**. `int a[5];` makes `a[0]` to `a[4]`.
* The size must be a constant expression greater than 0 (`BAD ARRAY SIZE`, error 29, otherwise). A size may be left out if a list of initial values gives it: `int w[] = { 7, 8, 9 };` has three elements.
* Elements may be of any type: `char`, `int`, `float`, pointers, structures, or other arrays. An array of arrays is a **multi-dimensional array**: `int t[2][3];` is two rows of three, and `t[1][2]` is the last element.
* `sizeof a` is the size in bytes, so `sizeof a / sizeof a[0]` is the number of elements.
* The name of an array, used in an expression, is the address of its first element, and can be given to a function that takes a pointer: `sum(a, 5)` (see [Pointers](#pointers)).
* **There are no checks.** An index outside the array reads or writes whatever is in the memory there, and nothing stops the program. This is C.

```c
// expect: exit 0
// screen: 0 sum 21 last 6
// screen: 1 12 6
int t[2][3] = { { 1, 2, 3 }, { 4, 5, 6 } };
int main(void)
{
    int i, j, s = 0;
    for (i = 0; i < 2; i++)
        for (j = 0; j < 3; j++)
            s += t[i][j];
    cls();
    printf("sum %d last %d\n", s, t[1][2]);
    printf("%d %d\n", sizeof t, sizeof t[0]);
    return 0;
}
```

An array of `char` holds a string when its last element is a 0 (see [Strings](#strings)). A global or `static` array starts as zeros unless you give it values; an array declared inside a function without `static` holds whatever was in that memory, and **cannot be given initial values** (make it `static`, or assign the elements; see [Initialisers](#initialisers)).

An array declared inside a function lives on the stack, which is small: the locals of one function may add up to no more than 255 bytes (see [Functions](#functions)). For a bigger array, declare it at the top of the program (or `static`), or take the memory from the [heap](#heap).

One object, array or not, must fit in one region of the compiled image: the largest is 8,192 bytes (see [Memory](#memory)).

**See also** [Initialisers](#initialisers), [Pointers](#pointers), [Strings](#strings), [Structures](#structures).

---

## BREAK

BREAK is **CAPS SHIFT + SPACE**. Hold both keys while a program is running and it stops. The report rows show `BREAK` and `LINE m`, and when you press a key the editor comes back with your program exactly as it was, the cursor on line *m*: the line where the function that was running starts.

BREAK works anywhere a program can be: in a tight loop, in `pause()`, during a `beep()`, in `getkey()` and `gets()`, in the middle of a calculation. A BREAK that falls inside one of the ROM's own short uninterruptible sections (a `beep()`, a floating-point operation, a tape transfer) waits until that section ends, which is at once for a person.

* A program that BREAK interrupts leaves nothing to repair: the next `RUN` starts again with a new, empty heap and fresh static data.
* While a tape block moves, the interrupts that read the keyboard are off, so the tape routines look at SPACE themselves; SPACE, or BREAK, then stops `tape_save()` and `tape_load()` and ends the program with `BREAK` (see [Tapes](#tapes)).
* In the editor BREAK does nothing. At a `LIST` page it ends the listing. At a tape command (`SAVE`, `LOAD`, `VERIFY`, `LIB`) it stops the tape and the report is `BREAK`.
* BREAK shows in the exit report as `BREAK`, not as a number, although internally it is runtime error 5 (see [Appendix C](08_appendices.md#appendix-c-runtime-errors)).

**See also** [Errors](#errors), [Tapes](#tapes), `exit` in [Part 4](04_library.md#exit).

---

## Characters

**char is unsigned.** A `char` is one byte holding 0 to 255, and `char c = 255;` stays 255, which prints as 255 and is not less than 0. It is widened to an `int` by adding a zero byte (`c + 1` is 256 when `c` is 255). If you want a signed byte, say `signed char`: it holds -128 to 127 and is widened by copying the sign. `unsigned char` is the same as `char`. Putting a larger number into a `char` keeps its low 8 bits.

**Character constants** are written in single quotes, and have the type `int` and the character's code as value: `'A'` is 65. Exactly one character, or one escape, may stand between the quotes; an empty or longer one is `BAD CHARACTER CONSTANT` (error 13). The escapes are the same in character constants and in strings:

| Escape | Code | Escape | Code |
|---|---|---|---|
| `\n` | 10 (new line) | `\a` | 7 |
| `\t` | 9 | `\b` | 8 |
| `\r` | 13 | `\f` | 12 |
| `\0` | 0 | `\v` | 11 |
| `\\` | 92 | `\'` | 39 |
| `\"` | 34 | `\xhh` | the hexadecimal code |
| `\ooo` | the octal code | | |

Any other escape, or a `\x` without digits, or a code over 255, is `BAD ESCAPE` (error 14).

```c
// expect: exit 0
// screen: 0 256 0 65 10
// screen: 1 ok 92 65 65
// screen: 2 -56
int main(void)
{
    char c = 255;
    signed char s = 200;
    int n = c + 1;
    c++;
    cls();
    printf("%d %d %d %d\n", n, c, 'A', '\n');
    printf("%c%c %d %d %d\n", 'o', 107, '\\', '\101', '\x41');
    printf("%d\n", s);
    return 0;
}
```

**The character set.** Source text is made of the printable ASCII characters, codes 32 to 126, and the end of a line. A character outside the set, or one that is no C token (`@`, `$` and the backquote), is `BAD CHARACTER` (error 10). On the screen:

* codes 32 to 126 have a glyph;
* codes 128 to 143 are the **block graphics**, the 16 patterns of a character cell made of four quarters (bit 0 the top-right quarter, bit 1 the top-left, bit 2 the bottom-right, bit 3 the bottom-left);
* codes 144 to 164 print the 21 **user-defined graphics**, eight bytes each from the table at `$F180` (the start clears the table, so they show as spaces until a program writes them);
* any other code shows as a space.

`getkey()` and `gets()` return ASCII, and the editor's control codes: 1 to 4 for the cursor keys, 8 for DELETE and 13 for ENTER. The eight characters C needs that the TS2068 keyboard does not have, `[ ] { } | ~ ^ \`, are typed with SYMBOL SHIFT and a letter (see [The editor](#the-editor)). The whole set is in [Appendix D](08_appendices.md#appendix-d-character-set-and-keyboard).

**See also** [Strings](#strings), [Screen](#screen), [Types](#types), `putchar` and `getkey` in [Part 4](04_library.md).

---

## Compiling

Leap-C is a **compiler**. Your program is kept as plain text: the lines exactly as you typed them. When you type `RUN` on the empty last line, the ROM

1. shows `COMPILING` on the status row;
2. reads the whole text and translates it into **Z80 machine code**, in memory (the *image*);
3. clears the screen, starts the program at `main`, and runs it at the full speed of the machine;
4. when the program ends, leaves its screen as it is and shows a **report** on rows 22 and 23 until you press a key.

```
Hello, TS2068!

...
EXIT 0
IMAGE 39 B  HEAP 18340 B
```

`EXIT 0` is the value `main` returned (or the argument of `exit()`), shown as a signed number; a `void main` shows `EXIT 0`. `IMAGE` is the size of the compiled program, its code and its static data together; `HEAP` is the largest block `malloc()` could give the program (see [Heap](#heap)). The command `FREE` shows the same two figures for the last compile, and how much room is left for the source (see [Memory](#memory)).

**The compile stops at the first error.** There is no list of errors: the report is `ERROR n: MESSAGE` with the line, the editor comes back with the cursor at the place where the compiler gave up, and you correct that one and run again. Nothing has been executed, so there is nothing to undo.

```c
// expect: error E_UNDECL 4
int main(void)
{
    return a + b;
}
```

Only the first of the two mistakes, the undeclared `a`, is reported. See [Errors](#errors).

**The image is not saved.** The compiled code is built again at every `RUN` and thrown away when you edit; `SAVE` writes only the source text. The source is what `LIST` shows, so the program always appears as you wrote it.

**Compile speed** is about 13 ms per line (13.4 ms over the test corpus), so a program of 50 lines compiles in under a second, and an 850-line program, the largest typical one, in about 11 seconds.

**Where the code goes.** The compiler fills four regions of memory in order, code from the bottom up and data from the top down. If the program does not fit in all four, the compile stops with `ERROR 101: PROGRAM TOO BIG`; if the source and the compiler's tables do not fit together, with `ERROR 100: OUT OF MEMORY`. Both are explained in [Memory](#memory).

**See also** [Errors](#errors), [Memory](#memory), [Programs](#programs), `RUN` and `FREE` in [Part 3](03_keywords.md#run).

---

## Conversions

C converts values from one type to another whenever a calculation or an assignment needs it. Leap-C follows C89 with its 16-bit `int`.

* **Integer promotions.** A `char` becomes an `int` before it is used in a calculation: an unsigned `char` by adding a zero byte, a `signed char` by copying its sign.
* **The usual arithmetic conversions.** When two operands differ, they are made the same: if either is `unsigned`, both become `unsigned`; otherwise both are `int`. **Unsigned wins.** This matters for comparisons: `-1 < 1u` is *false*, because -1 as an unsigned number is 65535.
* **Comparison, `/`, `%` and `>>`** use the signed or the unsigned operation according to the converted type.
* **Floating point.** If either operand of an arithmetic operator is `float`, the other is converted to `float` first. `3 / 2` is the integer division, 1; `3 / 2.0` is 1.5. An integer converts to `float` exactly, whatever its value. A `float` converts to an integer by **dropping the fraction** (truncating toward zero: 7.9 becomes 7 and -7.9 becomes -7) and keeping the low 16 bits of the integer part, or 8 for a `char`; a value outside the range gives no error. There is no conversion between `float` and a pointer, not even with a cast (`TYPE MISMATCH`).
* **Assignment, arguments and return values** convert to the type of the destination, the declared parameter type or the function's return type, when the compiler knows it: from `int` to `char` the low 8 bits are kept, from `float` to `int` the fraction is dropped. A call to a function that has no prototype passes its arguments as they are.
* **Pointers.** Adding to a pointer scales by the size of the element; the difference of two pointers is divided by it and is an `int`. A pointer converts to and from `void *` without a cast; between other pointer types you need a cast, or the compile stops with `TYPE MISMATCH`. Casts also work between integers and pointers.

```c
// expect: exit 0
// screen: 0 0 1 65535
// screen: 1 7 -7 1.00 1.50
// screen: 2 44
int main(void)
{
    int a = -1, n = 7.9, m = -7.9, big = 300;
    unsigned b = 1;
    float f = 3 / 2, g = 3 / 2.0;
    char c = big;
    cls();
    printf("%d %d %u\n", a < b, a < 1, a);
    printf("%d %d %.2f %.2f\n", n, m, f, g);
    printf("%d\n", c);
    return 0;
}
```

Here `a < b` is false because `b` is unsigned and so `a` is converted to 65535, while `a < 1` compares two `int`s and is true.

**See also** [Floating point](#floating-point), [Numbers](#numbers), [Types](#types), [Pointers](#pointers).

---

## Differences from standard C

Leap-C compiles a **subset of C89** (ANSI C), roughly Small-C plus `unsigned`, `struct`, `enum`, `typedef`, function pointers, multi-dimensional arrays and `float`. Whatever is outside the subset is a compile error, `ERROR 1: NOT SUPPORTED`, and never a silent miscompilation. These are the places where Leap-C differs from the C you may know:

| | Standard C | Leap-C |
|---|---|---|
| `int` | 16 bits or more | 16 bits: -32768 to 32767; overflow **wraps around** |
| `long`, `long double`, `union`, `volatile` | exist | **not supported** (`NOT SUPPORTED`); suffix `L` too |
| `char` | signed or unsigned | **unsigned**; `signed char` and `unsigned char` are accepted |
| integer division by zero | undefined | the quotient is **0** and the remainder 0; no error, no stop |
| `float`, `double` | IEEE 4 and 8 bytes | **one type**, the Sinclair 5-byte format: about 9.6 digits, up to 1.7E38; not IEEE |
| floating overflow, division by zero | undefined or infinity | stops the program with runtime error 6 `NUMBER TOO BIG`; underflow gives 0 |
| maths library | `sqrt`, `sin`, `pow` ... | **none**; they are short to write in C |
| standard library | `stdio.h`, `stdlib.h`, `string.h` ... | only the built-in library of [Part 4](04_library.md): no `scanf`, `fopen`, `atof`, `qsort` |
| `#include` | needed for the library | not needed: `printf` and the rest are built in; `#include <leap.h>` is accepted and does nothing; any other `#include` is not supported |
| preprocessor | `#if`, `#ifdef`, `#error`, function-like macros | only `#define NAME text`, `#undef` and `#pragma hires` |
| redefining a macro | allowed if identical | `ALREADY DEFINED`, even with the same text: `#undef` it first |
| `//` comments | C99 | accepted (a Leap-C extension) |
| `printf` | `%e`, `%g`, flags, precision | `%d %u %x %c %s %%`, `%f` and `%.Nf`, and a width; **no flags** (`- 0 + #`), no `%e` or `%g`; any other letter prints the next argument as a character; the return value is undefined |
| declaring a library function | allowed | your own prototype of, say, `strlen` declares a **new** function that you must then define; leave library functions undeclared |
| your own function named like a library one | a clash | yours wins: a program's own declaration hides the library function |
| structures | copy, pass, return | no struct assignment, parameters or return values: use pointers and `memcpy` |
| local initialisers | arrays and structs too | scalars only; make arrays and structs `static`, or assign the elements |
| variadic functions of your own | `...` | not supported; only `printf` takes a variable number of arguments |
| old-style (K&R) function definitions | allowed | not supported; use the ANSI form |
| several source files | yes | one only; `extern` is a declaration within it |
| `main` | `int main(int argc, char **argv)` | `int main(void)` or `void main(void)`; its value is shown as `EXIT n` |
| `switch` | any integer | on `int`, `unsigned` or `char`; not on a `float` |
| `register`, `auto` | storage hints | accepted and ignored |
| `const` | read-only object | checked only for a direct assignment (`ASSIGNMENT TO CONST`); the data is not put in ROM |
| undeclared function called | C89: implicit `int f()` | the same; resolved when the definition appears; `UNDEFINED FUNCTION` if there is none |
| bounds and NULL checks | none | none: this is C |
| names | 31 significant (internal) | 31 significant; case-sensitive |
| stack | large | `$F800-$FEFF`, 1,792 bytes; deep recursion stops with runtime error 1 |
| `malloc` | any size | up to about 18 KB, less as the source grows; `NULL` for 32 KB or more; `free(NULL)` does nothing |
| `memcpy` | overlap undefined | copes with overlap, like `memmove` |
| `abs(-32768)` | undefined | -32768 |
| lines | any length | at most 127 characters |

Some things you may expect that **do** work: the whole of C89's expression operators, short-circuit `&&` and `||`, `?:`, the comma operator, compound assignment, `sizeof`, casts, `goto`, `switch`, recursion, `enum`, `typedef`, structures and pointers to them, pointers to functions, arrays of any dimension, and `float`.

**See also** [Types](#types), [The preprocessor](#the-preprocessor), [Floating point](#floating-point), [Errors](#errors).

---

## Errors

There are two kinds.

**Compile errors** are found by `RUN` **before anything runs**. The compile stops at the first one. The report rows show

```
ERROR 23: UNDECLARED IDENTIFIER
LINE 5  'cont'
```

the number and message, and the line (counted from 1, the first line of the program). For the errors about a name (21 `REDECLARED`, 22 `ALREADY DEFINED`, 23 `UNDECLARED IDENTIFIER`, 52 `NO SUCH MEMBER`, 70 `UNDEFINED FUNCTION` and 76 `UNDEFINED LABEL`) the report also gives the name, its first 15 characters. Press a key (once every key is up; see [The editor](#the-editor)) and the editor comes back with that line on the screen and the cursor **at the place where the compiler stopped**: just after the offending word, or at the end of the line when something is missing (a forgotten `;` belongs at the end of its line). When the parser expects a token and finds another, the error is reported at the line of the *previous* token, so a statement without its `;` is reported on its own line, not on the next.

```c
// expect: error E_UNDECL 5
int main(void)
{
    int count = 0;
    return cont;
}
```

reports `ERROR 23: UNDECLARED IDENTIFIER`, `LINE 5  'cont'`, with the cursor just after `cont`. (Without the `// expect` line the same mistake is on line 4.)

**Runtime errors** happen while the program is running. The program stops, the screen keeps what the program drew, and the report rows show

```
RUNTIME ERROR 4: BAD ARGUMENT
LINE 3
```

The line is where the **function that failed starts** (its first line), not the statement that failed; this is the line where the cursor lands, in column 0, when you press a key. If the place cannot be told (a failure in part of a function that runs on in the last image region), the report gives no line.

```c
// expect: rterror 4
// rtline: 3
void bad(void)
{
    sound(99, 0);
}
int main(void)
{
    bad();
    return 0;
}
```

The register number 99 is checked, so `sound()` stops the program with runtime error 4; the line reported is 3, where `bad` starts.

The six runtime errors:

| Number | Message | Cause |
|---|---|---|
| 1 | `STACK OVERFLOW` | recursion too deep, or too many large locals |
| 2 | `OUT OF HEAP` | (never raised in this release: `malloc` returns 0 instead) |
| 3 | `HI-RES IN USE` | `mode(1)` while the compiled program occupies `$6000-$77FF` |
| 4 | `BAD ARGUMENT` | a checked library argument out of range |
| 5 | (shown as `BREAK`) | BREAK pressed, or SPACE during a tape transfer |
| 6 | `NUMBER TOO BIG` | a float overflow or float division by zero |

Everything else is not checked: an array index outside its array, a null or wild pointer, a division by zero in integers (the answer is 0). A program that does these things goes on, and may crash the machine.

The compile errors are in groups of tens:

| Numbers | Group |
|---|---|
| 1 | not supported |
| 10-17 | characters and numbers |
| 20-29 | declarations |
| 40-42 | types |
| 50-55 | expressions |
| 70-76 | statements and functions |
| 90-92 | limits |
| 100-101 | memory |

The full list, with the cause of each, is [Appendix B](08_appendices.md#appendix-b-compile-error-codes); the runtime errors are [Appendix C](08_appendices.md#appendix-c-runtime-errors); the other reports (`SAVED`, `BAD TAPE VERSION` ...) are in [Appendix A](08_appendices.md#appendix-a-reports-and-messages).

**See also** [BREAK](#break), [Compiling](#compiling), [The editor](#the-editor).

---

## Expressions

An expression is a calculation that gives a value. The operators, in order of **precedence** (what is worked out first), highest first:

| Rank | Operators | Worked out |
|---|---|---|
| 1 | `( )` calls, `[ ]`, `.`, `->`, postfix `++` `--` | left to right |
| 2 | unary `+ - ! ~ * &`, prefix `++ --`, `sizeof`, casts | right to left |
| 3 | `*` `/` `%` | left to right |
| 4 | `+` `-` | left to right |
| 5 | `<<` `>>` | left to right |
| 6 | `<` `<=` `>` `>=` | left to right |
| 7 | `==` `!=` | left to right |
| 8 | `&` | left to right |
| 9 | `^` | left to right |
| 10 | `\|` | left to right |
| 11 | `&&` | left to right |
| 12 | `\|\|` | left to right |
| 13 | `?:` | right to left |
| 14 | `=` `+=` `-=` `*=` `/=` `%=` `<<=` `>>=` `&=` `^=` `\|=` | right to left |
| 15 | `,` | left to right |

Note that `==` binds tighter than `&`: `6 & 3 == 2` is `6 & (3 == 2)`, which is 0. When in doubt, use brackets.

* `&&` and `||` are **short-circuit**: the right side is worked out only when the left side has not already decided the answer. `x && f()` does not call `f` when `x` is 0.
* `/` truncates toward zero and the sign of `%` is the sign of the dividend: `-7 / 2` is -3 and `-7 % 2` is -1. A division or remainder by zero gives 0.
* `>>` on a signed value is an arithmetic shift (the sign is kept).
* A comparison or a logical operator gives 1 or 0.
* **Constant expressions** are worked out by the compiler, so they cost nothing at run time; C requires them for array sizes, `case` labels, `enum` values, static initialisers and `sizeof`. The compiler also folds constant operands of `+ - * & | ^ << >>`.
* Floating operands are allowed with `+ - * /` and their assignments, the comparisons, `! && || ?:`, unary `+ -`, `++ --`, casts and `sizeof`. `% << >> & | ^ ~` on a `float` is `BAD OPERAND TYPE`.
* Nesting has limits (see [Appendix E](08_appendices.md#appendix-e-limits)): the compiler stops with `NESTING TOO DEEP` (error 90) after 112 levels of brackets, or 60 operands held at once, or 60 nested calls.

```c
// expect: exit 0
// screen: 0 7 9 5 1
// screen: 1 9 0 -3 -1
// screen: 2 1 0 1
int calls;
int touch(void)
{
    calls++;
    return 1;
}
int main(void)
{
    int x;
    cls();
    printf("%d %d %d %d\n", 1 + 2 * 3, (1 + 2) * 3, 10 - 2 - 3, 7 >> 1 + 1);
    printf("%d %d %d %d\n", 1 << 3 | 1, 6 & 3 == 2, -7 / 2, -7 % 2);
    x = 0 && touch();
    x = 1 || touch();
    printf("%d %d ", x, calls);
    x = 1 && touch();
    printf("%d\n", calls);
    return 0;
}
```

The two `touch()` calls on the short-circuit lines do not happen; the third does.

**See also** [Conversions](#conversions), [Numbers](#numbers), [Pointers](#pointers); the operators in [Part 3](03_keywords.md#arithmetic-operators).

---

## Floating point

`float` and `double` are the **same type**: the 5-byte number format of the TS2068 ROM, also used by Sinclair BASIC. It is not the IEEE format.

* About **9.6 significant digits** (a 32-bit mantissa). The largest magnitude is about **1.7E38**; the smallest, 2.9E-39; anything smaller is 0. There are no infinities, NaNs or denormals, and no negative zero.
* **Integers convert exactly**; converting to an integer drops the fraction (see [Conversions](#conversions)).
* **Constants** are written `1.5`, `1.`, `.5`, `1e5`, `2.5E-3`; the suffixes `f F l L` are accepted and change nothing. A constant above 1.7E38 is `NUMBER TOO LARGE`; a malformed one (`1e`, `1.5ff`, `1e5u`, `1..2`) is `BAD NUMBER`.
* **Printing.** `printf("%f", x)` prints 6 decimals, `%.2f` two, up to `%.9f` nine; every digit before the point is printed (up to 39), rounded half up; a width right-aligns. There is no `%e` or `%g`.
* **No maths library.** There is no `sqrt`, `sin`, `exp` or `pow`, and no `atof`. The usual functions are short in C (Newton's method for the square root takes a few lines; see [Part 7](07_examples.md)).
* **Overflow.** A result beyond 1.7E38 or a division by zero stops the program with **runtime error 6**, `NUMBER TOO BIG`; in a constant expression it is the compile error `NUMBER TOO LARGE`.
* **Not exact.** Decimal fractions such as 0.1 cannot be held exactly in binary, so adding ten tenths does not give exactly 1. Compare floats with a tolerance, not with `==`.
* A float takes 5 bytes (`sizeof(float)` is 5), a float local 5 of the 255 bytes of locals, and a float argument three words of stack.

```c
// expect: exit 5
// screen: 0 5 2 -2
// screen: 1 78.54 0.33
int main(void)
{
    float r = 5.0, a;
    a = 3.14159265 * r * r;
    cls();
    printf("%d %d %d\n", sizeof(float), (int)2.7, (int)-2.7);
    printf("%.2f %.2f\n", a, 1.0 / 3);
    return sizeof(double);
}
```

```c
// expect: rterror 6
int main(void)
{
    float big = 1.0e38;
    big = big * 10;
    return 0;
}
```

**Floating point is slow.** The calculation is done in software, in the ROM's own routines. The times, from measurement, include the cost of switching to them (about 1,580 T-states):

| Operation | T-states | Time |
|---|---:|---:|
| compare | 1,261 | 0.4 ms |
| add | 2,125 | 0.6 ms |
| subtract | 2,942 | 0.8 ms |
| negate | 629 | 0.2 ms |
| integer to float | 1,947 | 0.6 ms |
| float to integer | 4,883 | 1.4 ms |
| multiply | 20,090 | 5.7 ms |
| divide | 36,111 | 10.2 ms |
| `%.6f` print | 24,463 | 6.9 ms |

(An addition that must shift the mantissa to line the numbers up takes up to 9,773 T-states, 2.8 ms.) The T-state counts are the same in every emulator and on the real machine. A loop that multiplies a thousand times takes some six seconds: use integers where you can.

**See also** [Conversions](#conversions), [Numbers](#numbers), [Types](#types), `printf` in [Part 4](04_library.md#printf).

---

## Functions

A function is a named piece of program that can be called with arguments and can give back a value.

```c
int fact(int n)
{
    return n <= 1 ? 1 : n * fact(n - 1);
}
```

* **Definitions** are in the ANSI form, with the parameter types in the brackets. The old K&R form is not supported. Every parameter of a definition needs a name (`BAD PARAMETER`).
* **Prototypes are optional.** A function may be called before it is defined; if there is no prototype, it is declared implicitly as `int f()` and the compiler matches it with the definition when it comes. When a prototype or a definition is known, the number of arguments is checked (`WRONG ARGUMENT COUNT`, error 55) and each argument is converted to the parameter's type.
* **Parameters:** up to **16** (`TOO MANY PARAMETERS`, error 92). Scalars, floats and pointers can be passed and returned. Structures cannot (`NOT SUPPORTED`): pass a pointer.
* **Locals** are on the stack, and the locals of one function may take up to **255 bytes** in all. More is `FRAME TOO LARGE` (error 91): make the big array `static`, a global, or take it from the [heap](#heap).
* **Recursion** is supported. A function with one `int` parameter and one `int` local uses about 10 bytes of stack per level, so about **190 levels** can be reached from `main`; with no parameter and no local, 381; with four parameters and ten locals, 47. Too deep and the program stops with runtime error 1, `STACK OVERFLOW`, rather than overwrite memory.
* **Function pointers** can be declared, assigned, called through, kept in arrays and passed as arguments. The library's functions have addresses too.
* **Variadic functions** cannot be written; only `printf` takes any number of arguments.
* A function that is called and never defined is `UNDEFINED FUNCTION` (error 70), reported with its name at the line of its first use.
* **`main`.** The program starts at `main`; without it, `RUN` says `NO MAIN FUNCTION` (error 71). Write `int main(void)` or `void main(void)`. The value `main` returns is shown as `EXIT n`. `exit(n)` ends the program from any depth, with the same report.

```c
// expect: exit 0
// screen: 0 120 8 14
int apply(int (*f)(int), int x)
{
    return f(x);
}
int twice(int n)
{
    return n * 2;
}
int main(void)
{
    int (*fp)(int) = twice;
    cls();
    printf("%d %d %d\n", fact(5), apply(fp, 4), fp(7));
    return 0;
}
int fact(int n)
{
    return n <= 1 ? 1 : n * fact(n - 1);
}
```

`fact` is called before its definition, with no prototype at all.

**See also** [Names](#names), [Pointers](#pointers), [Programs](#programs); `exit` in [Part 4](04_library.md#exit); `return` in [Part 3](03_keywords.md#return).

---

## Heap

The **heap** is memory a program can ask for while it runs, with `malloc` and give back with `free`.

* `p = malloc(n);` returns the address of a block of at least `n` bytes, or **0 (a null pointer)** when nothing fits. It also returns 0 for a request of 32 KB or more. Always test the result.
* `free(p);` gives the block back. `free(0)` does nothing. Freeing a pointer that did not come from `malloc`, or freeing twice, is not checked, and damages the heap.
* The heap is the part of the source region that the source does not use: from the end of your program text to `$BFFE`. It is therefore **bigger when the program is shorter**: about 18,316 bytes for a minimal program, and only a few hundred when the source is nearly 18 KB. The `HEAP` figure of the report after `RUN`, and of `FREE`, is the largest block `malloc` can return (`malloc(h)` succeeds and `malloc(h + 1)` gives 0).
* The blocks are searched first-fit, and neighbouring free blocks are joined as `malloc` passes them. Each block has a 2-byte header, so the usable room is slightly smaller than the heap.
* **Every run starts with a new, empty heap.** A program that does not free its memory does not leak it into the next run, and a program stopped by BREAK or an error leaves nothing to repair.

```c
// expect: exit 0
// screen: 0 ok 10 20
int main(void)
{
    int *p = malloc(2 * sizeof(int));
    char *q = malloc(40000);
    cls();
    if (!p || q)
        return 1;
    p[0] = 10;
    p[1] = 20;
    printf("ok %d %d\n", p[0], p[1]);
    free(p);
    free(0);
    return 0;
}
```

The result of `malloc` is a `void *`, which converts to any object pointer without a cast.

**See also** [Memory](#memory), [Pointers](#pointers), [Structures](#structures); `malloc` and `free` in [Part 4](04_library.md#malloc).

---

## High resolution

The TS2068 has a second display file at `$6000-$77FF` (6,144 bytes), and a **high-resolution colour mode** that uses it. `mode(1)` switches to that mode and `mode(0)` back to the normal one; any other argument stops the program with runtime error 4. The end of a program, however it ends, restores mode 0.

The memory at `$6000-$77FF` is also the last of the four regions the compiler fills with your program (see [Memory](#memory)). Only a large program reaches it, but if it does, the program and the second display file would be in the same place. So:

* **Put `#pragma hires` at the top of any program that uses `mode(1)`.** It reserves `$6000-$77FF` so that the compiler never puts code or data there; the price is that the largest program becomes 6,144 bytes smaller, 13,696 bytes of image. If the program then no longer fits, the compile stops with `PROGRAM TOO BIG`.
* `mode(1)` succeeds while nothing of the program is in that region. If something is there, because the program is large and has no pragma, `mode(1)` stops the program with **runtime error 3**, `HI-RES IN USE`.
* A pragma placed late cannot take back what the compiler has already put in the region: code that already runs there stays, and `mode(1)` then fails. That is why the pragma belongs at the top.

```c
// expect: exit 0
#pragma hires
int main(void)
{
    mode(1);
    plot(0, 0);
    mode(0);
    return 0;
}
```

**See also** [Memory](#memory), [Screen](#screen), `#pragma` in [Part 3](03_keywords.md#pragma), `mode` in [Part 4](04_library.md#mode).

---

## Initialisers

An initialiser gives a variable its first value: `int a = 5;`, `char name[] = "Leap";`.

* **Global and `static` variables** take constant expressions, and everything C89 allows: scalars; arrays and structures in braces, with braces nested or left out (*brace elision*); a trailing comma; a list shorter than the array (the rest is zero); an array whose size is left out (`[]`), which takes its size from the list; `char` arrays from a string (a string that exactly fills the array may leave out its 0 byte); addresses of objects, array elements, members, functions, and a string plus an offset. Floating variables take constant arithmetic (integers converted), and integer variables may be set from floating constants (truncated). Without an initialiser they start as zero.
* **Local variables** may be given any expression, but only **scalars**: `int b = a * 3;`, `int k = { 6 };`. A local array or structure cannot have an initialiser (`NOT SUPPORTED`): declare it `static` (it is then initialised once, before `main`), or assign its elements. A local without an initialiser has no value yet.
* Static data is set up before `main` starts, and every `RUN` starts it again from the initial values.

```c
// expect: exit 0
// screen: 0 5 2 0 0
// screen: 1 Leap 5
// screen: 2 3 6
int v[5] = { 1, 2 };
int w[] = { 7, 8, 9 };
char name[] = "Leap";
int main(void)
{
    int a = 2, b = a * 3;
    cls();
    printf("%d %d %d %d\n", sizeof v / sizeof v[0], v[1], v[3], v[4]);
    printf("%s %d\n", name, sizeof name);
    printf("%d %d\n", sizeof w / sizeof w[0], b);
    return 0;
}
```

An initialiser that is wrong (too many elements, a string too long for its array) is `BAD INITIALISER` (error 28).

**See also** [Arrays](#arrays), [Strings](#strings), [Structures](#structures), [Numbers](#numbers).

---

## Memory

This concept explains where your program and its data live, and what `FREE` and the report after `RUN` tell you.

### The memory map

The TS2068's 64 KB is used like this:

| Range | Bytes | Holds |
|---|---:|---|
| `$4000-$5AFF` | 6,912 | the screen: display file 1 and the attributes |
| `$5B00-$5D59` | 602 | the system variables |
| `$5D5A-$5FFF` | 678 | Leap-C's own working cells |
| `$6000-$77FF` | 6,144 | display file 2 (high-resolution mode) **or** image region 4 |
| `$7800-$BFFF` | 18,432 | the **source**, the compile workspace, and the **heap** |
| `$C000-$DFFF` | 8,192 | image region 1 |
| `$E000-$F17F` | 4,480 | image region 2 |
| `$F180-$F3FF` | 640 | the user-defined graphics, the editor's line, and other platform cells |
| `$F400-$F7FF` | 1,024 | image region 3, **or** a loaded library |
| `$F800-$FEFF` | 1,792 | the stack, where the locals live |

The full map is in [Appendix F](08_appendices.md#appendix-f-memory-map).

### The source

Your program is stored as the lines you typed, one after another from `$7800` upward. Each line costs its length in characters plus **3 bytes**, and that includes the spaces you indented it with. The source region is 18,432 bytes, and the compiler's tables share it, so the largest program is about **18 KB of source**: a minimal program leaves room for 18,412 bytes of lines, and a typical program of 850 lines (13 KB of text) fits. `FREE` shows the room that is left. The editor says `PROGRAM FULL` when a line does not fit.

### The image

The compiled program, **code and static data**, is called the image. It has its own memory in four regions, and 19,840 bytes in all:

| Region | Addresses | Bytes |
|---|---|---:|
| 1 | `$C000-$DFFF` | 8,192 |
| 2 | `$E000-$F17F` | 4,480 |
| 3 | `$F400-$F7FF` | 1,024 |
| 4 | `$6000-$77FF` | 6,144 |

The compiler fills region 1 first, then 2, 3 and 4. In each, **code grows upward from the bottom and data downward from the top**; when a region is full, the code goes on in the next one, joined by a jump, so a function or a loop can span two regions. Each *object* of data (a global, a `static` local, a string literal, an array) goes whole into the first region with room for it, from the top down. An object never spans two regions, so the largest single object is **8,192 bytes**, the size of region 1.

Two things take a region away:

* a **loaded library** occupies region 3, so the program is 1 KB smaller (see [Part 6](06_libraries.md));
* `#pragma hires` reserves region 4 (see [High resolution](#high-resolution)).

### The reports

After a successful `RUN`, and in answer to `FREE`, the report rows are

```
SOURCE s B  FREE f B
IMAGE i B  HEAP h B
```

`SOURCE` is the size of the source in the line store, `FREE` the room left for it; `IMAGE` the bytes of code and data of the last compile (0 before the first), not counting a region that a library or the pragma closed; `HEAP` the largest block the program could take with `malloc`.

### Two ways to run out

* `ERROR 100: OUT OF MEMORY`: the **source and the compiler's tables** no longer fit together in the source region. Shorten the program. Each name the compiler learns costs workspace (13 bytes for a global scalar, a local or a member, 20 for an array, 24 for a two-parameter prototype), and each `switch` case 6 bytes. For ordinary programs this is the limit that bites first: the typical program above uses 12.7 KB of image and about 7 KB of the image's room stays unused.
* `ERROR 101: PROGRAM TOO BIG`: the **compiled code and data** do not fit in the four regions. Shorten the code, or move data out of the image into the heap.

### The stack

The stack is `$F800-$FEFF`, 1,792 bytes, and the locals of every function live on it. Calls go on until the stack is within `$F900`; one more call stops the program with runtime error 1.

**See also** [Compiling](#compiling), [Heap](#heap), [High resolution](#high-resolution), [Functions](#functions), [Appendix E](08_appendices.md#appendix-e-limits), [Appendix F](08_appendices.md#appendix-f-memory-map).

---

## Names

A name (an *identifier*) is a letter or underscore followed by letters, digits and underscores. It names a variable, a function, a type, a structure tag, an `enum` constant, a macro or a label.

* **Case matters.** `count` and `Count` are different names, and so are `main` and `Main`. The keywords are lower case.
* Names are significant to **31 characters**.
* A keyword cannot be used as a name, and neither as a macro name.
* The library's names (`printf`, `strlen`, ...) are **not reserved**. An identifier that nothing in your program declares is looked up among them; a declaration of your own comes first and hides the library function.

**Scope** is the part of the program where a name can be used.

* A name declared outside every function is global, from its declaration to the end of the program.
* A name declared inside a function, or in a block (between `{` and `}`), is local to it, and may **hide** a name of the same spelling declared outside. Declarations in a block come at its start.
* A `static` local keeps its value from one call to the next, and starts at zero. A `static` global is private to the program (there is only one file anyway).
* Labels for `goto` belong to the function; a `goto` to a label the function does not define is `UNDEFINED LABEL` (error 76).
* A name declared twice in one scope is `REDECLARED` (error 21); one never declared is `UNDECLARED IDENTIFIER` (error 23).

```c
// expect: exit 0
// screen: 0 1 2 1
// screen: 1 5 7
// screen: 2 3 0
int x = 1;
int abs(int n)
{
    return n < 0 ? 0 : n;
}
int counter(void)
{
    static int n;
    n++;
    return n;
}
int main(void)
{
    int count = 5, Count = 7;
    cls();
    printf("%d ", x);
    {
        int x = 2;
        printf("%d ", x);
    }
    printf("%d\n", x);
    printf("%d %d\n", count, Count);
    counter();
    counter();
    printf("%d %d\n", counter(), abs(-5));
    return 0;
}
```

Inside the block, `x` is the local 2; outside, the global 1 again. The program's own `abs` hides the library's, so `abs(-5)` is 0 here.

**See also** [Functions](#functions), [The preprocessor](#the-preprocessor), [Types](#types).

---

## Numbers

**Integers.** An `int` is 16 bits, two's complement: -32768 to 32767. An `unsigned` is 0 to 65535. Calculations **wrap around**: 32767 + 1 is -32768, and 0u - 1 is 65535. There is no error. Multiplying 1000 by 1000 gives 16960 (the low 16 bits of a million).

**Integer constants** are written in decimal (`255`), hexadecimal (`0xFF`), octal (a leading 0: `010` is 8) or as a character (`'A'`). A constant runs from 0 to 65535; a larger one is `NUMBER TOO LARGE` (error 16), and the minus sign is an operator (`-5` is the constant 5 negated). A suffix `u` or `U` is accepted; `l` and `L` are not supported. An invalid digit or suffix is `BAD NUMBER` (error 15).

**Division** truncates toward zero, and `%` takes the sign of the dividend. **Integer division by zero gives 0**, and so does `%` by zero: there is no error and the program does not stop.

```c
// expect: exit 0
// screen: 0 -32768 0 255 8
// screen: 1 65535 0 0
// screen: 2 16960
int zero = 0;
int main(void)
{
    int big = 32767, k = 1000;
    cls();
    printf("%d %d %d %d\n", big + 1, 0x10 * 16 - 256, 0xFF, 010);
    printf("%u %d %d\n", 65535, 100 / zero, 100 % zero);
    printf("%d\n", k * k);
    return 0;
}
```

**Floating constants** have a decimal point or an exponent (see [Floating point](#floating-point)). `08.5` and `09e1` are decimal floats, since a leading 0 only means octal for an integer.

**Other limits to know:** `abs(-32768)` is -32768. `atoi` skips spaces and control characters, takes an optional sign and decimal digits, and wraps beyond 16 bits. `rand()` returns 0 to 32767. `itoa(n, buf, base)` works in bases 2 to 36 (lower-case letters) and writes a minus sign only in base 10.

**See also** [Conversions](#conversions), [Expressions](#expressions), [Floating point](#floating-point), [Types](#types), the operators in [Part 3](03_keywords.md#arithmetic-operators).

---

## Pointers

A pointer holds the **address** of something in memory. It is 16 bits, so it can point anywhere in the 64 KB: there are no far pointers.

* `&x` is the address of `x`; `*p` is the thing `p` points to. `p->m` is `(*p).m` for a structure.
* **Pointer arithmetic scales.** If `p` points to an `int`, `p + 1` points to the next `int`, 2 bytes on; `q - p`, the difference of two pointers into the same array, is the number of elements between them, an `int`. `p[i]` is `*(p + i)`.
* `void *` points to anything. `malloc` returns one, and it converts to and from any object pointer without a cast. Other pointer types need a cast to be assigned to each other.
* **A null pointer is 0.** `if (p == 0)`, or `if (!p)`, tests for it, and `malloc` returns it when nothing fits. The examples in this manual write it as 0.
* A pointer may be cast to and from an integer, which gives access to any address: `*(char *)0x5800 = 0x3A;` stores a byte in the attributes. The functions `inp` and `outp` do the same for the I/O ports.
* **There are no checks.** Leap-C does not know where an array ends, and a null or wild pointer is used as it stands: writing through a wrong address can change the program, the screen or the stack. This is C.
* A **pointer to a function** is declared `int (*fp)(int);`, assigned a function's name and called as `fp(7)` (see [Functions](#functions)).

```c
// expect: exit 0
// screen: 0 20 30 2
// screen: 1 6
int a[4] = { 10, 20, 30, 40 };
int main(void)
{
    int *p = a + 1;
    int *q = &a[3];
    char *s = "Leap-C";
    int n = 0;
    cls();
    printf("%d %d %d\n", *p, *(p + 1), q - p);
    while (*s++)
        n++;
    printf("%d\n", n);
    return 0;
}
```

**See also** [Arrays](#arrays), [Heap](#heap), [Strings](#strings), [Structures](#structures), [Conversions](#conversions); the operators in [Part 3](03_keywords.md#pointer-and-address-operators).

---

## Programs

A Leap-C program is C: declarations of variables, types and functions, one after another, and a function called `main`, where it starts. There are no statements outside functions.

* A program is typed in the editor, one **line** at a time. A line is at most **127 characters**, and a string literal must be wholly on one line, at most 126 characters. There is no TAB key: indent with spaces (they count in the 18 KB).
* The editor keeps the lines as text, `[length][text][end of line]`, in the source store, from `$7800` up. `LIST` shows them, `SAVE` writes them to tape, and `RUN` compiles them. See [Memory](#memory).
* A program starts with the screen as the editor left it, so call `cls()` before printing. The print colours are paper 7 (white) and ink 0 (black); the heap is empty; the static data is as initialised (or 0); `rand()` starts the sequence of `srand(1)`.
* A program ends when `main` returns, when it calls `exit(n)`, when a runtime error stops it, or when you press BREAK. The AY sound chip is silenced, the screen mode is normal again, and the report appears.
* **`RUN`, `LIST`, `FREE`, `NEW`, `SAVE`, `LOAD`, `VERIFY` and `LIB` are not part of C.** They are commands, typed alone on the empty line after the last line of the program (see [The editor](#the-editor)).
* Comments are `/* ... */`, which may span lines, and `// ...` to the end of the line.

```c
// expect: exit 4
void finish(int code)
{
    exit(code);
}
int main(void)
{
    finish(4);
    return 0;
}
```

`exit` ends the program from inside `finish`; the report is `EXIT 4`.

**See also** [Compiling](#compiling), [Functions](#functions), [Memory](#memory), [The editor](#the-editor).

---

## Screen

The screen is 24 rows of 32 characters, and 256 by 192 pixels.

* **Text:** rows 0 to 23, columns 0 to 31. Row 0 is the top. `at(row, col)` moves the print position (a row beyond 23 becomes 23; the column is taken modulo 32), `tab(col)` moves along the current row. Text goes on at the start of the next row after column 31, and below row 23 the screen scrolls up. `'\n'` moves to the start of the next row. `cls()` clears the screen to the current colours and puts the print position at row 0, column 0.
* **Pixels:** x from 0 to 255 and y from 0 to 191, counted **from the top left**: `plot(0, 0)` is the top left corner, `plot(255, 191)` the bottom right. This is the other way up from Sinclair BASIC. `plot` and `draw` outside the screen do nothing (a `draw` moves its ends to the edge); `point(x, y)` is 1 if the pixel is set and 0 if not, or off the screen.
* **Attributes:** each character cell (8 by 8 pixels) has one attribute byte: *flash* 128, *bright* 64, *paper* times 8, plus *ink*. `attr(row, col)` reads it, and is 0 outside the screen. Printing, `plot`, `draw` and `cls` use the current colours; `plot` gives its cell the print attribute.
* **Colours** are the numbers 0 to 7:

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| black | blue | red | magenta | green | cyan | yellow | white |

* `ink(n)`, `paper(n)` and `border(n)` take 0 to 7 (the number is masked to 3 bits). `bright(n)`, `flash(n)`, `inverse(n)` and `over(n)` take 0 or 1 (masked to 1 bit). `inverse(1)` swaps ink and paper in the attribute of what you print or plot (a plotted pixel is still set); `over(1)` makes printing and plotting exclusive-or, so a second call erases what the first drew.
* `sprite_get(row, col, w, h, buf)` and `sprite_put(...)` copy a rectangle of character cells to and from memory, 9 bytes a cell (8 pixel rows, then the attribute), row by row. A rectangle not wholly on the screen, or an empty one, is runtime error 4.
* The screen is **memory**: display file 1 is at `$4000-$57FF` (the pixels) and the attributes follow at `$5800-$5AFF`, so a pointer can read and change it directly.
* A program's screen stays after it ends, until you press a key. The border returns to white.

```c
// expect: exit 0
// screen: 2     HI
// attr: 2 4 0xB1
int main(void)
{
    cls();
    ink(1);
    paper(6);
    flash(1);
    at(2, 4);
    print("HI");
    return 0;
}
```

The attribute at row 2, column 4 is flash (128) plus paper 6 (48) plus ink 1: 177, hexadecimal B1.

```c
// expect: exit 1
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 0 191 0
// pixel: 7 5 1
// attr: 0 0 0x3A
int main(void)
{
    cls();
    plot(0, 0);
    plot(255, 191);
    *(char *)0x5800 = 0x3A;
    *(char *)0x4500 = 1;
    return point(255, 191) + point(0, 191) + point(300, 5);
}
```

Here the pixels are plotted from the top, and two bytes of the screen are stored through pointers: the attribute of cell (0, 0) becomes ink 2 on white (`0x3A`), and the byte at `$4500` is the eight pixels at y = 5 beginning at x = 0 (bit 0 is x = 7). The program returns 1: `point(255, 191)` is 1, the other two 0.

**See also** [Characters](#characters), [High resolution](#high-resolution), the screen functions in [Part 4](04_library.md#cls) and [Appendix D](08_appendices.md#appendix-d-character-set-and-keyboard).

---

## Sound

The TS2068 has an **AY-3-8912** sound chip with three tone channels, A, B and C, and one noise generator. Leap-C reaches it in two ways.

* `beep(frames, semitone)` plays a note on channel A for that many frames (a frame is a 60th of a second on a TS2068: see [Time](#time)) and waits for it to finish. The semitone is counted from middle C, which is 0: 12 is the C an octave above, -12 the C an octave below. The range is -60 to 69; below -39 the note is A0, the lowest; outside the range the program stops with runtime error 4. A `frames` of 0 plays nothing. BREAK ends a beep early.
* `sound(reg, value)` writes the AY register `reg` (0 to 15; another number is runtime error 4) with the low 8 bits of `value`. The registers are the chip's own:

| Register | Controls |
|---|---|
| 0, 1 | channel A pitch: low 8 bits, high 4 bits |
| 2, 3 | channel B pitch |
| 4, 5 | channel C pitch |
| 6 | noise period |
| 7 | mixer (which channels play tone and noise) |
| 8, 9, 10 | volume of channels A, B, C |
| 11, 12 | envelope period |
| 13 | envelope shape |
| 14, 15 | the chip's input/output ports |

The chip's data sheet explains the registers. When a program ends, however it ends, the volume of all three channels is set to 0, so a sound does not go on into the editor.

```c
// expect: exit 0
// ay: 0=100 1=2 2=50
int main(void)
{
    beep(5, 0);
    sound(0, 100);
    sound(1, 2);
    sound(2, 50);
    return 0;
}
```

**See also** [Time](#time), `beep` and `sound` in [Part 4](04_library.md#beep), [BREAK](#break).

---

## Statements

A statement is one step of a function. All of C89's are there.

* An **expression statement** ends with `;`. A **block** is statements in `{ }`, with its declarations at the start.
* `if (c) s1 else s2`, `while (c) s`, `do s while (c);` and `for (a; b; c) s` work as in C. A `for` cannot declare its variable (that is C99): declare it before.
* `switch (e) { case 1: ... break; default: ... }` works on `int`, `unsigned` and `char`. A `case` label must be a constant; a value twice, or a second `default`, is `DUPLICATE CASE`, and a `case` outside a `switch` is `MISPLACED CASE`. Without `break`, control runs on into the next case.
* `break` leaves the nearest loop or `switch`, `continue` goes to the next turn of a loop; outside one they are `MISPLACED BREAK` and `MISPLACED CONTINUE`.
* `goto label;` jumps to `label:` in the same function. `return` leaves the function, with a value if it has one.

```c
// expect: exit 0
// screen: 0 one two other
int main(void)
{
    int i;
    cls();
    for (i = 0; i < 3; i++) {
        switch (i) {
        case 0:
            print("one ");
            break;
        case 1:
            print("two ");
            break;
        default:
            print("other");
        }
    }
    return 0;
}
```

**See also** [Expressions](#expressions), [Functions](#functions); the statements in [Part 3](03_keywords.md#for).

---

## Strings

C has no string type. A **string** is an array of `char` that ends with a 0 byte.

* A string literal, `"Leap"`, is stored in the program's static data with its 0 added: 5 bytes. Adjacent literals are joined, `"ab" "cd"` being `"abcd"`. A literal is at most 126 characters and must end on its line (`UNTERMINATED STRING`, error 12, otherwise).
* `char name[] = "Leap";` makes an array of 5 bytes. `char *s = "Leap";` makes a pointer to the literal. `char buf[16];` is room for a string of up to 15 characters, because of the 0.
* Everything on strings is done by library functions: `strlen`, `strcpy`, `strncpy`, `strcmp`, `strcat` and `strchr`, and `memcpy`, `memmove`, `memset` and `memcmp` for plain memory. They work as in C, **without any checking** of the size of what they write. Characters are compared as unsigned numbers.
* `gets(buf, max)` reads a line from the keyboard, with DELETE to correct it, at most `max - 1` characters and a 0, and returns `buf`. `atoi` and `itoa` convert between strings and integers; `printf` with `%s` prints a string and `%d` and the others build text.
* `"..."` escapes are those of [Characters](#characters).

```c
// expect: exit 0
// screen: 0 abcd 4
// screen: 1 Leap-C ok
char buf[16];
int main(void)
{
    char *s = "ab" "cd";
    cls();
    printf("%s %d\n", s, strlen(s));
    strcpy(buf, "Leap");
    strcat(buf, "-C");
    printf("%s %s\n", buf, strcmp(buf, "Leap-C") == 0 ? "ok" : "no");
    return buf[4] != '-';
}
```

**See also** [Arrays](#arrays), [Characters](#characters), [Pointers](#pointers); the string functions in [Part 4](04_library.md#strlen).

---

## Structures

A **structure** groups values of different types under one name.

```c
struct person { char name[8]; int age; };
```

* The members are laid end to end, with **no padding**: the size is the sum of the sizes of the members (this `struct person` is 10 bytes). `sizeof` gives it. A member is reached with `.`, or with `->` through a pointer.
* Members can be of any complete type: arrays, other structures, pointers. A structure may contain a **pointer to itself**, which is how lists and trees are made (see [Part 7](07_examples.md)). A structure that is not yet defined is an `INCOMPLETE TYPE`; a member name that is not there is `NO SUCH MEMBER`.
* **Not in this release:** you cannot assign a structure to another, pass one to a function, or return one. Use a **pointer**, and copy with `memcpy(&to, &from, sizeof from)`.
* A global or `static` structure may have an initialiser in braces; a local one may not (see [Initialisers](#initialisers)).
* There are no unions.

```c
// expect: exit 0
// screen: 0 3 10
// screen: 1 Ada 36
struct pair { char tag; int n; };
struct person { char name[8]; int age; };
struct person people[2];
void set(struct person *p, char *name, int age)
{
    strcpy(p->name, name);
    p->age = age;
}
int main(void)
{
    struct person copy;
    cls();
    set(&people[0], "Ada", 36);
    memcpy(&copy, &people[0], sizeof copy);
    printf("%d %d\n", sizeof(struct pair), sizeof(struct person));
    printf("%s %d\n", copy.name, copy.age);
    return 0;
}
```

`struct pair` is 3 bytes, a `char` and an `int` with nothing between them.

**See also** [Arrays](#arrays), [Heap](#heap), [Pointers](#pointers), [Types](#types), `struct` in [Part 3](03_keywords.md#struct), `memcpy` in [Part 4](04_library.md#memcpy).

---

## Tapes

Leap-C uses the cassette interface for three kinds of tape, which are different and do not mix: **program tapes**, **data tapes** and **library tapes**.

* **Program tapes.** `SAVE "name"` writes the program's **source** to tape, in two blocks, a header and the data, in the format of the TS2068's own cassettes. The name is 1 to 10 characters. `LOAD "name"` reads a program back, replacing the one in the editor; `LOAD ""` reads the next program tape, whatever it is called; `VERIFY "name"` compares a tape with the program, byte for byte, and writes nothing. `SAVE` of an empty program is `NO PROGRAM`. `tools/c2tape.py`, on a PC, makes a program tape from a `.c` file. The compiled image is never saved: the source is the program.
* **Data tapes.** A running program saves and loads its own data with `tape_save(name, addr, len)` and `tape_load(name, addr, max)`: `len` bytes from any address, in memory of any kind, as a tape of the data type. A name is 1 to 10 characters; a longer one, an empty name for `tape_save`, or `len` 0, is runtime error 4.
* **Library tapes.** `LIB "name"` loads a library of assembly functions (see [Part 6](06_libraries.md)).

`LOAD` skips data and library tapes, `tape_load()` skips program and library tapes, and `LIB` skips the other two: tapes of other kinds go by as if they were not there. A tape not made for Leap-C (a TS2068 BASIC tape, or a tape of Leap V2) carries another **version word**, and is refused with `BAD TAPE VERSION` before anything is stored; Leap-C's tapes are likewise refused by the other two.

**What happens to your program when `LOAD` fails.** A program is received above your source and replaces it only when the whole tape has arrived sound, so a failed `LOAD` (`LOAD FAILED`, `BAD TAPE VERSION`, `BREAK`) leaves the program as it was. The one exception is a tape too long to be received above the source: it is received in place, and if it then fails the source is empty, as after `NEW`.

`tape_load(name, addr, max)` returns a number:

| Result | Meaning |
|---|---|
| 0 or more | the length loaded |
| -1 | nothing was loaded: no tape of that name within about 2 minutes, or the tape is longer than `max`; the memory at `addr` is untouched |
| -2 | the data failed after part of it had been stored |
| -3 | a tape that is not Leap-C's (nothing was stored) |

`tape_load` takes the first data tape of that name; with `""`, the first data tape of any name. `tape_save` returns when both blocks have been sent: about 7 seconds, and 5 to 7 milliseconds for each byte.

While a tape moves, the status row shows `SAVING name`, `LOADING` (or `VERIFYING`) while it searches, then `LOADING name` once the header is found. **BREAK, or SPACE, stops a tape command** (the report is `BREAK`) and ends `tape_save` or `tape_load` with runtime error 5, shown as `BREAK`. While a block moves the interrupts are off, so `frames()` does not count.

The search for a header gives up after 15 blocks it does not want or about 2 minutes of silence. How to work a tape in each emulator is in `EMULATORS.md`, and on the real machine in [Appendix G](08_appendices.md#appendix-g-hardware-notes).

```c
// expect: rterror 4
char data[4];
int main(void)
{
    tape_load("elevenchars", data, sizeof data);
    return 0;
}
```

A name of 11 characters is too long, and the program stops with runtime error 4 before the tape is touched.

A program that keeps a record between runs can be written like this (not run here, as it needs a tape):

```c
int n = tape_load("scores", table, sizeof table);
if (n < 0)
    n = 0;                  /* no tape, or a bad one: start empty */
```

**See also** [BREAK](#break), [Errors](#errors), `SAVE`, `LOAD`, `VERIFY` and `LIB` in [Part 3](03_keywords.md#save), `tape_save` and `tape_load` in [Part 4](04_library.md#tape_save), [Part 6](06_libraries.md).

---

## The editor

When Leap-C starts, the screen is white with a black **status row** at the bottom. There is no `OK` prompt: you are in the editor, which shows the program on rows 0 to 22, and row 23 is the status row.

* The status row shows `LINE n/m`: the line the cursor is on, and the number of lines. It also shows `COMPILING` and the tape messages, and carries three coloured squares, red, green and blue, at the right.
* You edit **one line at a time**. Type; move with the cursor keys; ENTER stores the line and goes on to the next. Moving off a line with UP or DOWN stores it too.
* A line longer than 32 characters **wraps** at its last space (or at the 32nd character) onto up to four rows. The cursor's line is always shown whole.
* A line that does not fit in the source store gives `PROGRAM FULL` and stays in the edit buffer.
* When you leave a line, the **C keywords in it turn bold**, so a misspelt `whlie` shows. Words that only contain a keyword (`int1`), other cases (`INT`), and anything in a string, character constant or comment stay plain.

| Key | Does |
|---|---|
| letters, digits, SPACE | type; CAPS SHIFT + letter gives a capital |
| SYMBOL SHIFT + key | punctuation (table below) |
| ENTER | store the line and go to the next |
| CAPS SHIFT + 5 / 8 | cursor left / right |
| CAPS SHIFT + 7 / 6 | cursor up / down (between the rows of a wrapped line first) |
| CAPS SHIFT + 0 (DELETE) | delete the character before the cursor; on an empty line, delete the line |
| CAPS SHIFT + 1 | delete the whole line |
| CAPS SHIFT + ENTER | insert an empty line before this one |
| BREAK (CAPS SHIFT + SPACE) | ignored in the editor; stops a program, a listing or a tape command |

The punctuation of C, typed with SYMBOL SHIFT and a key (the first eight are Leap-C's own, the rest are the TS2068's):

| `[` Y | `]` U | `{` F | `}` G | `\|` S | `~` A | `^` H | `\` D |
|---|---|---|---|---|---|---|---|
| `!` 1 | `@` 2 | `#` 3 | `$` 4 | `%` 5 | `&` 6 | `'` 7 | `(` 8 |
| `)` 9 | `_` 0 | `"` P | `;` O | `:` Z | `<` R | `>` T | `?` C |
| `=` L | `+` K | `-` J | `*` B | `/` V | `,` N | `.` M | |

Two-character operators are typed one character at a time: `<=` is SYMBOL SHIFT + R, then SYMBOL SHIFT + L. Two letters pressed together type nothing.

**Commands.** A command is typed **alone on the empty line after the last line** of the program (the *append line*), in upper or lower case. Anything else there becomes a new line of the program. `RUN` compiles and runs; `LIST` shows the program a page at a time (a key shows the next page, BREAK ends the listing); `FREE` shows the memory; `NEW` clears the program; `SAVE`, `LOAD`, `VERIFY` and `LIB` work with the tape. A word that begins like a command but is not one (`save(x);`) is source. See [Part 3](03_keywords.md#run).

**After a report, press a key once every key is up.** Every command ends with a report on rows 22 and 23, which stays until you press a key. Leap-C ignores a key that was still held from the command (the ENTER of `RUN`, or BREAK), and drops a key that was latched meanwhile, so a report cannot vanish before you read it: **let go of everything, then press one key**. The key is not typed. Then the editor is redrawn with your program as it was; after a compile error or a runtime error the cursor is on the line, and at the place the report gave.

**See also** [Compiling](#compiling), [Errors](#errors), [Programs](#programs), [Part 3](03_keywords.md#run), [Appendix D](08_appendices.md#appendix-d-character-set-and-keyboard).

---

## The preprocessor

The preprocessor changes the program text before the compiler reads it. In Leap-C it is small, and does only a few things. A directive is a `#` that is the first token on its line.

* **`#define NAME replacement`** defines an object-like macro: wherever `NAME` appears afterwards as a word, the replacement, the rest of its line, stands instead. The replacement is checked for lexical errors where it is defined, and expanded where it is used. A macro's own name inside its expansion stays a plain name, so a macro cannot call itself. Macros may use other macros, nested up to 8 deep, and one expansion makes at most 255 tokens (`NESTING TOO DEEP` beyond).
* **`#undef NAME`** forgets it. Defining a macro that already exists is `ALREADY DEFINED` (error 22), even if the text is the same; `#undef` it first.
* **`#include <leap.h>`** (or `"leap.h"`) is accepted and does **nothing**, because the library is built in. Any other `#include` is not supported.
* **`#pragma hires`** reserves the memory of the high-resolution screen (see [High resolution](#high-resolution)). Any other pragma, or one with anything after `hires`, is an error. It is the only pragma.
* Function-like macros (`#define f(x)`), `#if`, `#ifdef`, `#error`, `#line` and the rest are `NOT SUPPORTED`. The names of macros are names: a keyword cannot be one.

A macro is expanded where it is *used*, so changing it between two functions changes what they see:

```c
// expect: exit 0
// screen: 0 9 16
#include <leap.h>
#define N 3
#define SQ (N * N)
int first(void)
{
    return SQ;
}
#undef N
#define N 4
int second(void)
{
    return SQ;
}
int main(void)
{
    cls();
    printf("%d %d\n", first(), second());
    return 0;
}
```

```c
// expect: error E_REDEF 3
#define N 1
#define N 1
int main(void)
{
    return N;
}
```

The second `#define N` is `ALREADY DEFINED`, reported on line 3 (the report gives no name for a `#define`).

Because there is no `#if`, there is no include guard or conditional compilation: write the one program you want. Constants are better as `enum` values or as macros; text such as `"hello"` is better as a string.

**See also** [Differences from standard C](#differences-from-standard-c), [Names](#names), `#define`, `#undef` and `#pragma` in [Part 3](03_keywords.md#define).

---

## Time

Time is counted in **frames**, the unit of `frames()`, `pause(n)` and the length of a `beep()`.

* `frames()` returns the frame count as an `unsigned` number; it goes round to 0 after 65,535, which on a TS2068 is every 18 minutes. Subtracting two readings gives the elapsed frames correctly even across the wrap.
* `pause(n)` waits `n` frames, and `pause(0)` returns at once. BREAK ends a pause.
* **A frame is 1/60 s on a TS2068**, and in Fuse and TSRun. ZEsarUX 13.0 emulates the TS2068 with the 50 Hz frame of a British Spectrum:

| | TS2068, Fuse, TSRun | ZEsarUX 13.0 |
|---|---|---|
| `frames()` counts per second | 60 | 50 |
| `pause(60)` lasts | 1 s | 1.2 s |
| `beep(30, 0)` lasts | 0.5 s | 0.6 s |

* Programs run at the same speed on both machines (3.528 MHz; a 60 Hz frame is 58,688 T-states); only time measured in frames differs.
* Every frame is counted, also while floating-point code runs. **While a tape block moves, `frames()` does not count**, since interrupts are off.

```c
// expect: exit 1
int main(void)
{
    unsigned t = frames();
    pause(6);
    return frames() - t >= 6;
}
```

**See also** [Sound](#sound), [Floating point](#floating-point), `frames` and `pause` in [Part 4](04_library.md#frames).

---

## Types

| Type | Bytes | Range or meaning |
|---|---:|---|
| `char`, `unsigned char` | 1 | 0 to 255 (**unsigned**) |
| `signed char` | 1 | -128 to 127 |
| `int`, `short`, `signed` | 2 | -32768 to 32767; wraps around |
| `unsigned`, `unsigned int`, `unsigned short` | 2 | 0 to 65535; wraps around |
| pointer | 2 | an address, 0 to 65535; no far pointers |
| `enum` | 2 | the constants are `int` |
| `float`, `double` | 5 | the one Sinclair floating type: about 9.6 digits, up to 1.7E38 |
| array | n times the element | any element type, including arrays |
| `struct` | the sum of the members | no padding |
| `void` | -- | function results, and `void *` |
| function | -- | definitions, prototypes, pointers to functions |

* `typedef` gives a new name to any type: `typedef unsigned word;`.
* `enum colour { RED, GREEN = 5, BLUE };` makes constants of type `int`: RED is 0, GREEN 5 and BLUE 6. Values go on from the last one.
* `const` is accepted, and checked for a direct assignment only. `static` and `extern` work as described under [Names](#names); `register` and `auto` are ignored.
* **Not supported** (`NOT SUPPORTED`): `long`, `long double`, `union`, `volatile`.
* An object cannot be larger than 65,535 bytes (`TYPE TOO LARGE`, error 42), and one in the image no larger than 8,192; a local variable area no larger than 255 bytes.
* `sizeof` gives the size in bytes, at compile time.

```c
// expect: exit 0
// screen: 0 1 2 2 2 2 5
// screen: 1 0 5 6 65535
// screen: 2 0
typedef unsigned word;
enum colour { RED, GREEN = 5, BLUE };
int main(void)
{
    word w = 65535;
    cls();
    printf("%d %d %d %d %d %d\n", sizeof(char), sizeof(int), sizeof(short),
           sizeof(unsigned), sizeof(char *), sizeof(float));
    printf("%d %d %d %u\n", RED, GREEN, BLUE, (unsigned)-1);
    w++;
    printf("%u\n", w);
    return 0;
}
```

**See also** [Conversions](#conversions), [Characters](#characters), [Floating point](#floating-point), [Numbers](#numbers), [Structures](#structures), `typedef` and `enum` in [Part 3](03_keywords.md#typedef).
