# Part 4 -- The library

The functions that are built into Leap-C, in alphabetical order. They are the whole of what a program can use besides the C language itself: printing, colour, the keyboard, pixels and lines, sound, time, strings, the heap, the I/O ports and the tape.

You do not declare them and you do not include anything. Type `cls();` and it is there. (`#include <leap.h>` is accepted, for the sake of programs written elsewhere, and does nothing.)

**Do not declare a library function yourself.** In ordinary C you may write `int strlen(char *s);` at the top of a program; in Leap-C that line declares a *new* function called `strlen`, which you must then define. Leave the library's functions undeclared and call them. The library's names are not reserved: a function or variable of your own with the same name hides the library's, and from then on that name is yours. The library's functions have addresses, so `unsigned (*len)(void *) = strlen;` works.

**Coordinates.**

| | Range | Origin |
|---|---|---|
| text rows | 0 to 23 | row 0 is the top |
| text columns | 0 to 31 | column 0 is the left |
| pixel *x* | 0 to 255 | 0 is the left edge |
| pixel *y* | 0 to 191 | 0 is the **top** edge |

Pixels are counted from the top left, as text is; this is not the Sinclair BASIC convention, in which *y* counts up from the bottom.

**Frames.** A *frame* is one display refresh: 1/60 second on a TS2068, 1/50 second on ZEsarUX. `frames()`, `pause()` and `beep()` count frames, so a program that waits 60 frames waits one second on a TS2068 and 1.2 seconds on ZEsarUX.

**Arguments.** The compiler knows every function's parameters. A call with the wrong number of arguments is `ERROR 55: WRONG ARGUMENT COUNT`, and an integer where a pointer is wanted (or a pointer where an integer is wanted) is `ERROR 40: TYPE MISMATCH`. The one exception is `printf`, which takes any number of arguments. An integer parameter accepts any integer (a `char` or an `unsigned` too); a pointer parameter accepts a pointer to any object. A function that returns `void` gives no value: assigning its result is `ERROR 40: TYPE MISMATCH`, and using it in an expression (`f() + 1`) is `ERROR 51: BAD OPERAND TYPE`.

**Checked arguments.** A few functions check an argument and stop the program if it is out of range: `beep`'s semitone, `sound`'s register, `mode`'s number, `itoa`'s base, the rectangle of `sprite_get` and `sprite_put`, and the name or length of `tape_save` and `tape_load`. The report is `RUNTIME ERROR 4: BAD ARGUMENT` and `LINE m`, where *m* is the line on which the function that made the call **starts**. See [Appendix C](08_appendices.md#appendix-c-runtime-errors). Everything else is unchecked: an array subscript, a pointer, the size of a buffer you pass to `strcpy`. That is C.

**Printing.** Text is printed at the *print position*. After a character the position moves one column right; after column 31 it goes to column 0 of the next row, and below row 23 the whole screen scrolls up one row. The character `'\n'` (10) moves to the start of the next row. A character that has no picture is shown as a space. Codes 128 to 143 are the block graphics (see `putchar`). A program starts with the screen as the editor left it, so **call `cls()` first** whenever it prints. At the start of every run the colours are ink 0 (black) and paper 7 (white), with bright and flash off.

## How to read an entry

Each entry gives the C **prototype** of the function, its **kind**, a description, a tested example and, where they matter, notes, the errors it can cause, and related entries.

| Notation | Meaning |
|---|---|
| `int abs(int n)` | the function's C prototype: result type, name, parameters |
| *italics* | in the description, a parameter's name |
| `void` result | the function gives no value: use it as a statement |
| `...` | any number of further arguments (only `printf`) |

Every entry here is a **function**. The prototypes show the type that the function treats each argument as; to the compiler every integer parameter is an `int` and every pointer parameter accepts any object pointer, so `memset(buf, 0, 100)` and `strcpy(name, "Leap")` need no casts. Where a prototype says `unsigned` (a count or a length), a value above 32767 is meant to be unsigned: 40000 is 40000, not -25536.

The examples are complete programs: type one in, `RUN` it. Lines that begin `// expect:`, `// screen:`, `// attr:`, `// pixel:`, `// ay:` and `// keys:` are ordinary comments to the compiler, and you may leave them out. They state what the build checks every time it runs the example on the release ROM: the value `main` returns (`// expect: exit N`), the text on a screen row, a character cell's attribute byte, a pixel, a sound-chip register, and the keys typed into the program. An attribute byte is `flash * 128 + bright * 64 + paper * 8 + ink`. Examples that begin `// expect: rterror 4` show a program that stops with runtime error 4.

## Summary

| Group | Functions |
|---|---|
| **Text** | `cls`, `putchar`, `puts`, `print`, `printf`, `at`, `tab`, `ink`, `paper`, `border`, `bright`, `flash`, `inverse`, `over` |
| **Keyboard** | `getkey`, `inkey`, `gets` |
| **Graphics** | `plot`, `draw`, `point`, `attr`, `mode`, `sprite_get`, `sprite_put` |
| **Sound** | `beep`, `sound` |
| **Time** | `frames`, `pause`, `rand`, `srand` |
| **Strings and memory** | `strlen`, `strcpy`, `strncpy`, `strcmp`, `strcat`, `strchr`, `memcpy`, `memmove`, `memset`, `memcmp` |
| **Conversion** | `atoi`, `itoa`, `abs` |
| **Memory and ports** | `malloc`, `free`, `inp`, `outp` |
| **Program** | `exit` |
| **Tape** | `tape_save`, `tape_load` |

| Function | Does |
|---|---|
| `abs(n)` | the size of *n* without its sign |
| `at(row, col)` | moves the print position |
| `atoi(s)` | the number in a string |
| `attr(row, col)` | a character cell's attribute byte |
| `beep(frames, semitone)` | plays a note |
| `border(n)` | sets the border colour |
| `bright(n)` | bright on or off for printing and plotting |
| `cls()` | clears the screen |
| `draw(x0, y0, x1, y1)` | draws a line |
| `exit(status)` | ends the program |
| `flash(n)` | flash on or off |
| `frames()` | the frame counter |
| `free(p)` | gives back a block of the heap |
| `getkey()` | waits for a key |
| `gets(buf, max)` | reads a line of text |
| `ink(n)` | the ink colour |
| `inkey()` | the key pressed, if any |
| `inp(port)` | reads an I/O port |
| `inverse(n)` | swaps ink and paper |
| `itoa(n, buf, base)` | a number as text |
| `malloc(n)` | a block of the heap |
| `memcmp(a, b, n)` | compares memory |
| `memcpy(d, s, n)` | copies memory |
| `memmove(d, s, n)` | copies memory, overlap or not |
| `memset(p, c, n)` | fills memory |
| `mode(n)` | normal or high-resolution colour mode |
| `outp(port, value)` | writes an I/O port |
| `over(n)` | exclusive-or printing and plotting |
| `paper(n)` | the paper colour |
| `pause(n)` | waits *n* frames |
| `plot(x, y)` | sets a pixel |
| `point(x, y)` | tests a pixel |
| `print(s)` | prints a string |
| `printf(fmt, ...)` | formatted printing |
| `putchar(c)` | prints one character |
| `puts(s)` | prints a string and a new line |
| `rand()` | a random number |
| `sound(reg, value)` | writes a sound-chip register |
| `sprite_get(row, col, w, h, buf)` | copies a rectangle of the screen to memory |
| `sprite_put(row, col, w, h, buf)` | copies it back |
| `srand(seed)` | restarts the random numbers |
| `strcat(d, s)` | appends a string |
| `strchr(s, c)` | finds a character in a string |
| `strcmp(a, b)` | compares strings |
| `strcpy(d, s)` | copies a string |
| `strlen(s)` | the length of a string |
| `strncpy(d, s, n)` | copies at most *n* characters |
| `tab(col)` | moves to a column |
| `tape_load(name, addr, max)` | loads a data tape |
| `tape_save(name, addr, len)` | saves a data tape |

---

## abs

`int abs(int n)` -- **function**

The size of *n* without its sign: *n* if it is 0 or more, -*n* if it is less.

```c
// expect: exit 9
// screen: 0 5 0 -32768
int main(void)
{
    cls();
    printf("%d %d %d", abs(-5), abs(0), abs(-32768));
    return abs(-9);
}
```

**Notes.**

* `abs(-32768)` is -32768. The number 32768 does not exist in a 16-bit `int`, so the sign cannot be removed. (In C the result is undefined; here it is the two's complement result.)

**Errors.** None.

**See also** `itoa`, `atoi`.

---

## at

`void at(int row, int col)` -- **function**

Moves the print position, so that the next text printed starts at that *row* and *col*. Row 0 is the top of the screen, column 0 the left edge. `at` prints nothing.

```c
// expect: exit 0
// screen: 2      HERE
// screen: 5 AT
// screen: 23 LAST
int main(void)
{
    cls();
    at(2, 5);
    print("HERE");
    at(5, 0);
    print("AT");
    at(99, 0);
    print("LAST");
    return 0;
}
```

**Notes.**

* A *row* beyond 23 counts as 23, so `at(99, 0)` is the start of the bottom row. A *col* is taken modulo 32: `at(0, 33)` is column 1.
* `at` sets both numbers; `tab` sets only the column.
* The position is also moved by every character printed, and `cls()` puts it back at row 0, column 0.

**Errors.** None.

**See also** `tab`, `cls`, `print`.

---

## atoi

`int atoi(const char *s)` -- **function**

The whole number at the start of the string *s*: leading spaces and control characters are skipped, then an optional `+` or `-`, then decimal digits up to the first character that is not a digit.

```c
// expect: exit 7
// screen: 0 123 -45 0
int main(void)
{
    cls();
    printf("%d %d %d", atoi("123"), atoi("  -45xyz"), atoi("abc"));
    return atoi("+7");
}
```

**Notes.**

* A string with no digits gives 0.
* The result wraps around in 16 bits, as every `int` does: `atoi("65535")` is -1 and `atoi("70000")` is 4464. There is no error for a number that is too large.
* `atoi` reads whole numbers only; a decimal point ends the number.

**Errors.** None.

**See also** `itoa`, `gets`.

---

## attr

`int attr(int row, int col)` -- **function**

The attribute byte of the character cell at *row* (0 to 23) and *col* (0 to 31): the cell's colours as the screen holds them. The byte is `flash * 128 + bright * 64 + paper * 8 + ink`.

```c
// expect: exit 56
// screen: 0 114
// attr: 1 3 114
int main(void)
{
    cls();
    ink(2);
    paper(6);
    bright(1);
    at(1, 3);
    print("X");
    at(0, 0);
    printf("%d", attr(1, 3));
    return attr(23, 31);
}
```

The cell at row 1, column 3 has bright (64), paper 6 (48) and ink 2: 114. The corner cell was painted by `cls()` before the colours were chosen, so it keeps the plain 56: paper 7 (56) and ink 0.

**Notes.**

* A cell outside the screen gives 0.
* `attr` reads the cell, not the print attribute: use it to see what is on the screen, for instance after `plot` has changed a cell's colours.

**Errors.** None.

**See also** `ink`, `paper`, `bright`, `flash`, `point`, the concept [Screen](05_concepts.md#screen).

---

## beep

`void beep(int frames, int semitone)` -- **function**

Plays a note on channel A of the AY sound chip. *frames* is how long it sounds, in display frames (the prototype's *frames* is unsigned; 0 plays nothing). *semitone* is the pitch counted from middle C: 0 is middle C, 12 is the C above it, -12 the C below. The program waits until the note ends.

```c
// expect: exit 0
// ay: 0=165 1=1 8=0
int main(void)
{
    beep(8, 7);
    beep(8, 4);
    beep(8, 0);
    return 0;
}
```

This plays G, E, C, each for 8 frames. After the program ends, register 0 and 1 of the chip hold the period of the last note, middle C.

**Notes.**

* *semitone* may be -60 to 69. The chip cannot go lower than 27.5 Hz (the lowest A on a piano, semitone -39), so -60 to -40 all play that note.
* A frame is 1/60 second on a TS2068 and 1/50 second on ZEsarUX, so `beep(30, 0)` is half a second on one and 0.6 on the other.
* `beep` uses channel A only and leaves it silent (its volume register, 8, is 0) when the note ends.
* BREAK stops a long note and ends the program.

**Errors.** A *semitone* below -60 or above 69 is runtime error 4, BAD ARGUMENT, and plays nothing:

```c
// expect: rterror 4
int main(void)
{
    beep(1, 70);
    return 0;
}
```

**See also** `sound`, `pause`, `frames`, the concept [Sound](05_concepts.md#sound).

---

## border

`void border(int n)` -- **function**

Sets the colour of the border to *n*. The colours are 0 black, 1 blue, 2 red, 3 magenta, 4 green, 5 cyan, 6 yellow, 7 white.

```c
// expect: exit 0
int main(void)
{
    int c;
    for (c = 0; c < 8; c++) {
        border(c);
        pause(10);
    }
    border(7);
    return 0;
}
```

This steps the border through all eight colours, a sixth of a second each.

**Notes.**

* Only the low three bits of *n* count: `border(9)` is `border(1)`.
* `border` changes the border at once; it is independent of `ink` and `paper`.

**Errors.** None.

**See also** `ink`, `paper`, the concept [Screen](05_concepts.md#screen).

---

## bright

`void bright(int n)` -- **function**

Switches bright on (*n* odd) or off (*n* even) for everything printed, plotted or drawn from now on, and for the cells `cls()` paints. `bright(1)` is the brighter set of the eight colours.

```c
// expect: exit 0
// screen: 0 BN
// attr: 0 0 0x78
// attr: 0 1 0x38
int main(void)
{
    cls();
    bright(1);
    print("B");
    bright(0);
    print("N");
    return 0;
}
```

**Notes.**

* Only the low bit of *n* counts: `bright(2)` is `bright(0)` and `bright(3)` is `bright(1)`.
* Bright is bit 6 of a cell's attribute byte.
* A cell takes the print attribute when something is printed or plotted in it, or when the screen is cleared; changing `bright` does not change what is already on the screen.

**Errors.** None.

**See also** `flash`, `ink`, `paper`, `inverse`, `attr`.

---

## cls

`void cls(void)` -- **function**

Clears the whole screen to the current colours (paper and ink, bright and flash) and puts the print position at row 0, column 0.

```c
// expect: exit 0
// screen: 0 Hi
// attr: 0 0 0x31
// attr: 23 31 0x31
int main(void)
{
    ink(1);
    paper(6);
    cls();
    print("Hi");
    return 0;
}
```

The whole screen is now blue on yellow: ink 1 (blue) and paper 6 (yellow) make the attribute byte 6 * 8 + 1 = 49 (`0x31`) in every cell.

**Notes.**

* `inverse` is not applied by `cls`: the screen is painted with the plain ink and paper.
* A program starts with the screen as the editor left it. Call `cls()` before the first thing a program prints.

**Errors.** None.

**See also** `at`, `ink`, `paper`, `border`, the concept [Screen](05_concepts.md#screen).

---

## draw

`void draw(int x0, int y0, int x1, int y1)` -- **function**

Draws a straight line from the pixel (*x0*, *y0*) to the pixel (*x1*, *y1*). **Both end points are drawn.** *x* counts from the left (0 to 255), *y* from the top (0 to 191). The line takes the current ink, paper, bright and flash in every character cell it touches, and obeys `over`.

```c
// expect: exit 1
// pixel: 10 20 1
// pixel: 100 20 1
// pixel: 9 20 0
// pixel: 101 20 0
// pixel: 0 0 1
// pixel: 255 191 1
int main(void)
{
    cls();
    draw(10, 20, 100, 20);
    draw(0, 0, 255, 191);
    return point(50, 20);
}
```

**Notes.**

* The end points may be given in either order.
* A coordinate that is off the screen is moved to the nearest edge, so `draw(0, 0, 300, 0)` draws to the right-hand edge, x = 255. The line is then drawn between the moved points, which is not always the line you meant; keep coordinates on the screen if the slope matters.
* With `over(1)` the line is drawn by exclusive-or, so drawing it a second time erases it.
* To draw a single pixel use `plot`.

**Errors.** None.

**See also** `plot`, `point`, `over`, the concept [High resolution](05_concepts.md#high-resolution), and the loadable library [shapes](06_libraries.md) for `circle` and `box`.

---

## exit

`void exit(int status)` -- **function**

Ends the program at once, from any depth of calls, with *status* as its result: exactly as if `main` had returned *status*. The shell then reports `EXIT status`.

```c
// expect: exit 42
// screen: 0 start
void finish(int n)
{
    exit(n);
}
int main(void)
{
    cls();
    print("start");
    finish(42);
    print("never");
    return 0;
}
```

**Notes.**

* `exit` does not return; the statements after it are not run.
* A program that ends by returning from `main` ends the same way; `exit` is for ending it from inside other functions.

**Errors.** None.

**See also** `malloc`, the concept [Errors](05_concepts.md#errors).

---

## flash

`void flash(int n)` -- **function**

Switches flashing on (*n* odd) or off (*n* even) for everything printed, plotted or drawn from now on, and for the cells `cls()` paints. A flashing cell alternates between its two colours.

```c
// expect: exit 0
// screen: 0 FN
// attr: 0 0 0xB8
// attr: 0 1 0x38
int main(void)
{
    cls();
    flash(1);
    print("F");
    flash(0);
    print("N");
    return 0;
}
```

**Notes.**

* Only the low bit of *n* counts.
* Flash is bit 7 of a cell's attribute byte: 128 + 56 = 184 (`0xB8`) for black on white, flashing.

**Errors.** None.

**See also** `bright`, `inverse`, `attr`.

---

## frames

`unsigned frames(void)` -- **function**

The display frame counter: a number that goes up by one every frame (1/60 second on a TS2068, 1/50 on ZEsarUX), from 0 to 65535 and then round to 0 again.

```c
// expect: exit 1
// screen: 0 waited
unsigned t0, t1;
int main(void)
{
    cls();
    t0 = frames();
    pause(10);
    t1 = frames();
    print("waited");
    return t1 - t0 - 10 < 2;
}
```

The program returns 1 when `pause(10)` took 10 or 11 frames (a wait can begin part-way through a frame).

**Notes.**

* The result is `unsigned`. To time something, subtract two readings with unsigned arithmetic: `frames() - t0` is right even when the counter has wrapped around between them. (At 60 frames a second the counter wraps every 18 minutes.)
* The counter stops while a tape block is moving (`tape_save` and `tape_load`): interrupts are off then.
* Frames are counted while floating-point code runs.

**Errors.** None.

**See also** `pause`, `beep`, the concept [Time](05_concepts.md#time).

---

## free

`void free(void *p)` -- **function**

Gives back to the heap the block that `malloc` returned as *p*, so that a later `malloc` can use it again. `free(0)` (the null pointer) does nothing.

```c
// expect: exit 1
// screen: 0 heap
int main(void)
{
    char *p;
    char *q;
    p = malloc(20);
    strcpy(p, "heap");
    cls();
    puts(p);
    free(p);
    free(0);
    q = malloc(20);
    return q == p;
}
```

The block that was freed is the first free block that fits, so the second `malloc` returns it again.

**Notes.**

* *p* must be a pointer that `malloc` returned and that has not been freed already. Leap-C does not check: freeing anything else, or the same block twice, damages the heap.
* Free blocks that are next to each other are joined into one when `malloc` next searches past them, so freeing many small blocks does not leave the heap in pieces for ever.
* Do not use a block after freeing it.

**Errors.** None.

**See also** `malloc`, the concept [Memory](05_concepts.md#memory).

---

## getkey

`int getkey(void)` -- **function**

Waits until a key is pressed and gives its code. Letters, digits and symbols give their ASCII codes (`'a'` is 97, `'A'` is 65, `'0'` is 48); the other keys give the editor's control codes: 1 to 4 for the cursor keys, 8 for DELETE and 13 for ENTER.

```c
// keys: "y"
// expect: exit 121
// screen: 0 Y or N? y
int main(void)
{
    int k;
    cls();
    print("Y or N? ");
    k = getkey();
    putchar(k);
    return k;
}
```

**Notes.**

* Each call reads one key. To read the next key, call `getkey` again.
* BREAK (CAPS SHIFT + SPACE) stops the program while it waits.
* `getkey` does not echo the key. To type a line of text use `gets`.
* To look at the keyboard without waiting use `inkey`.

**Errors.** None.

**See also** `inkey`, `gets`, the concept [Characters](05_concepts.md#characters).

---

## gets

`char *gets(char *buf, int max)` -- **function**

Reads a line typed at the keyboard into the buffer *buf*, which holds *max* characters, and returns *buf*. The characters are shown as you type them, starting at the print position. DELETE removes the last character typed. ENTER ends the line: the text is finished with a NUL, the print position moves to the start of the next row, and `gets` returns.

```c
// keys: "Hello" ENTER
// expect: exit 5
// screen: 0 Name? Hello
// screen: 1 Hi Hello
char buf[20];
int main(void)
{
    cls();
    print("Name? ");
    gets(buf, 20);
    printf("Hi %s", buf);
    return strlen(buf);
}
```

**Notes.**

* At most *max* - 1 characters are stored, which leaves room for the NUL; more keys are ignored until ENTER. A *max* below 1 is treated as 1, so `gets` stores only the NUL.
* Only the printable characters (space to `~`) are stored. The cursor keys and other control keys are ignored.
* DELETE on an empty line does nothing.
* BREAK stops the program while `gets` waits.

**Compared with C.** Standard C's `gets` takes no size and is the classic buffer overflow; this one takes the size of the buffer, as `fgets` does, but does not store the new line.

**Errors.** None.

**See also** `getkey`, `inkey`, `atoi`.

---

## ink

`void ink(int n)` -- **function**

Sets the ink colour for everything printed, plotted or drawn from now on, and for the cells `cls()` paints. The colours are 0 black, 1 blue, 2 red, 3 magenta, 4 green, 5 cyan, 6 yellow, 7 white.

```c
// expect: exit 0
// screen: 0 RS
// attr: 0 0 0x3A
// attr: 0 1 0x39
int main(void)
{
    cls();
    ink(2);
    print("R");
    ink(9);
    print("S");
    return 0;
}
```

**Notes.**

* Only the low three bits of *n* count: `ink(9)` is `ink(1)`.
* Ink is bits 0 to 2 of a cell's attribute byte.
* Colours already on the screen do not change.

**Errors.** None.

**See also** `paper`, `bright`, `flash`, `inverse`, `border`, the concept [Screen](05_concepts.md#screen).

---

## inkey

`int inkey(void)` -- **function**

The code of the key pressed since the last call of `getkey`, `inkey` or `gets`, or 0 if none has been. It never waits. The codes are the same as for `getkey`.

```c
// keys: NONE NONE "q"
// expect: exit 113
// screen: 0 2
int main(void)
{
    int n = 0, k;
    cls();
    while ((k = inkey()) == 0)
        n++;
    printf("%d", n);
    return k;
}
```

This counts how many times `inkey` found no key before one was pressed. (In the test, the `// keys:` line feeds two empty looks and then the letter `q`; on a real machine the count is however many times the loop ran before you pressed a key.)

**Notes.**

* A key is remembered until it is read, so a quick tap between two calls of `inkey` is not missed.
* A program that wants to do something else while it waits for a key should call `inkey` in a loop, and `pause(1)` inside the loop to keep the loop from running flat out.

**Errors.** None.

**See also** `getkey`, `gets`, `pause`.

---

## inp

`int inp(int port)` -- **function**

Reads the Z80 I/O port whose 16-bit address is *port*, and gives the byte read (0 to 255).

```c
// expect: exit 0
// screen: 0 77
// ay: 0=77
int main(void)
{
    cls();
    outp(0xF5, 0);
    outp(0xF6, 77);
    outp(0xF5, 0);
    printf("%d", inp(0xF6));
    return 0;
}
```

This writes 77 into register 0 of the AY sound chip by way of its ports ($F5 selects a register, $F6 holds the data) and reads it back.

**Notes.**

* The whole 16-bit *port* number is used as the address. Leap-C does not check it. For the keyboard use `getkey`, `inkey` and `gets` rather than reading ports.

**Errors.** None.

**See also** `outp`, `sound`, `inkey`.

---

## inverse

`void inverse(int n)` -- **function**

Switches inverse on (*n* odd) or off (*n* even). While it is on, everything printed, plotted or drawn takes the cell's colours with ink and paper **swapped**.

```c
// expect: exit 0
// screen: 0 IN
// attr: 0 0 0x07
// attr: 0 1 0x38
int main(void)
{
    cls();
    inverse(1);
    print("I");
    inverse(0);
    print("N");
    return 0;
}
```

**Notes.**

* Only the low bit of *n* counts.
* `cls()` does not swap: the screen is painted in the plain ink and paper.
* `plot` and `draw` in inverse mode set their pixels as usual, but give the cell the swapped colours. This differs from Sinclair BASIC, where `INVERSE 1` makes `PLOT` clear a pixel; to clear a pixel in Leap-C, plot it again with `over(1)`.

**Errors.** None.

**See also** `ink`, `paper`, `over`, `attr`.

---

## itoa

`char *itoa(int n, char *buf, int base)` -- **function**

Writes the number *n* as text, in the number base *base*, into the buffer *buf*, finishes it with a NUL and returns *buf*. *base* may be 2 to 36; the digits above 9 are the lowercase letters `a` to `z`.

```c
// expect: exit 4
// screen: 0 ff
// screen: 1 -255
// screen: 2 101
// screen: 3 ffff
char s[20];
int main(void)
{
    cls();
    puts(itoa(255, s, 16));
    puts(itoa(-255, s, 10));
    puts(itoa(5, s, 2));
    puts(itoa(-1, s, 16));
    return strlen(itoa(1234, s, 10));
}
```

**Notes.**

* A minus sign appears only in base 10. In every other base *n* is treated as an unsigned 16-bit number: `itoa(-1, s, 2)` is sixteen ones.
* Make the buffer at least 17 characters long: sixteen binary digits and the NUL are the longest text there is.
* `itoa` is not standard C, but it is the usual way to write one.

**Errors.** A *base* below 2 or above 36 is runtime error 4, BAD ARGUMENT:

```c
// expect: rterror 4
char s[20];
int main(void)
{
    itoa(5, s, 37);
    return 0;
}
```

**See also** `atoi`, `printf`.

---

## malloc

`void *malloc(unsigned n)` -- **function**

Takes a block of *n* bytes from the heap and returns a pointer to its first byte, or 0 (the null pointer) if no free block is large enough. The contents of the block are not cleared. Give the block back with `free` when you have finished with it.

```c
// expect: exit 45
// screen: 0 sum 45
// screen: 1 1
int main(void)
{
    int *a;
    int i, sum = 0;
    cls();
    a = malloc(10 * sizeof(int));
    if (a == 0) {
        print("no room");
        return -1;
    }
    for (i = 0; i < 10; i++) {
        a[i] = i;
        sum += a[i];
    }
    printf("sum %d\n", sum);
    printf("%d", malloc(40000) == 0);
    free(a);
    return sum;
}
```

**Notes.**

* The heap is the memory above the compiled program. At the start of every run it is one large free block; its size is the `HEAP` figure in the report after `RUN`, up to about 18 KB for a small program and less as the source grows.
* A request is served from the **first** free block that is large enough (first fit). Each block costs two bytes more than you ask for, and sizes are rounded up to an even number.
* A request of 32 KB or more always gives 0. `malloc(0)` gives a block.
* The returned pointer converts to any pointer type without a cast: `int *a = malloc(20);`.
* **Always test for 0** when the size depends on the program: with no check, a pointer of 0 is written through and the program damages memory. Leap-C does not check pointers.

**Errors.** None: a failed request gives 0, not an error.

**See also** `free`, `memset`, the concept [Memory](05_concepts.md#memory).

---

## memcmp

`int memcmp(const void *a, const void *b, unsigned n)` -- **function**

Compares the first *n* bytes at *a* with the first *n* at *b*. The result is negative if the first byte that differs is smaller in *a*, positive if it is larger, and 0 if all *n* bytes are equal. The bytes are compared as unsigned numbers, 0 to 255; a NUL byte is compared like any other, so `memcmp` does not stop at the end of a string.

```c
// expect: exit 0
// screen: 0 1 0 1
int main(void)
{
    cls();
    printf("%d %d %d", memcmp("abc", "abd", 3) < 0,
                       memcmp("abc", "abc", 3),
                       memcmp("abd", "abc", 3) > 0);
    return memcmp("abc", "xyz", 0);
}
```

**Notes.**

* With *n* equal to 0 the result is always 0.
* Test the sign of the result (`< 0`, `== 0`, `> 0`), not a particular value.

**Errors.** None.

**See also** `strcmp`, `memcpy`.

---

## memcpy

`void *memcpy(void *d, const void *s, unsigned n)` -- **function**

Copies *n* bytes from the memory at *s* to the memory at *d*, and returns *d*.

```c
// expect: exit 1
// screen: 0 Leap-C
// screen: 1 Lxyp-C
char src[8] = "Leap-C";
char dst[8];
int main(void)
{
    cls();
    memcpy(dst, src, 7);
    puts(dst);
    memcpy(dst + 1, "xy", 2);
    puts(dst);
    return memcpy(dst, src, 7) == dst;
}
```

**Notes.**

* Leap-C's `memcpy` is the same function as `memmove`: it works correctly when the two blocks overlap.
* The destination must have room for *n* bytes. Nothing is checked.
* With *n* equal to 0 nothing is copied.

**Errors.** None.

**See also** `memmove`, `strcpy`, `memset`, the concept [Memory](05_concepts.md#memory).

---

## memmove

`void *memmove(void *d, const void *s, unsigned n)` -- **function**

Copies *n* bytes from *s* to *d*, as `memcpy` does, and returns *d*. The blocks may overlap, in either direction: the bytes arrive as if they had first been copied to a separate place.

```c
// expect: exit 6
// screen: 0 ABABCD
// screen: 1 ABCDCD
char s[8] = "ABCDEF";
int main(void)
{
    cls();
    memmove(s + 2, s, 4);
    puts(s);
    memmove(s, s + 2, 4);
    puts(s);
    return strlen(s);
}
```

The first call moves `ABCD` two places up the buffer; the second moves `ABCD` (now at positions 2 to 5) two places down again.

**Notes.**

* `memcpy` behaves identically in Leap-C; use `memmove` when you want the overlap to be part of what the program says.

**Errors.** None.

**See also** `memcpy`, `memset`.

---

## memset

`void *memset(void *p, int c, unsigned n)` -- **function**

Sets *n* bytes starting at *p* to the value *c*, and returns *p*.

```c
// expect: exit 5
// screen: 0 *****
// screen: 1 oo***
char s[8];
int main(void)
{
    cls();
    memset(s, '*', 5);
    s[5] = 0;
    puts(s);
    memset(s, 'o', 2);
    puts(s);
    return strlen(s);
}
```

**Notes.**

* Only the low 8 bits of *c* are used: `memset(p, 0x1FF, 3)` stores 255.
* With *n* equal to 0 nothing is stored.
* `memset(p, 0, n)` clears a block, for instance the memory `malloc` gave you.
* To fill a string you need to put the NUL in yourself, as above.

**Errors.** None.

**See also** `memcpy`, `malloc`.

---

## mode

`void mode(int n)` -- **function**

Chooses the display mode: `mode(0)` is the normal screen, `mode(1)` the TS2068's high-resolution colour mode (see the concept [High resolution](05_concepts.md#high-resolution)). The end of a program always puts the machine back in mode 0.

```c
// expect: exit 1
#pragma hires
int main(void)
{
    int n;
    mode(1);
    plot(10, 10);
    n = point(10, 10);
    mode(0);
    return n;
}
```

**Notes.**

* High-resolution mode uses the memory at `$6000` to `$77FF`, which is also where the compiler puts the end of a very large program. **A program that uses `mode(1)` should say `#pragma hires`**, as above, which keeps the compiled program out of that memory.
* `plot`, `draw` and `point` go on working in mode 1.

**Errors.**

| Mistake | What happens |
|---|---|
| *n* is neither 0 nor 1 | runtime error 4, BAD ARGUMENT |
| `mode(1)` when the compiled program occupies `$6000-$77FF` (a large program without `#pragma hires`) | runtime error 3, HI-RES IN USE |

```c
// expect: rterror 4
int main(void)
{
    mode(2);
    return 0;
}
```

**See also** `plot`, `point`, the concept [High resolution](05_concepts.md#high-resolution).

---

## outp

`void outp(int port, int value)` -- **function**

Writes the byte *value* (its low 8 bits) to the Z80 I/O port whose 16-bit address is *port*.

```c
// expect: exit 0
// ay: 2=100
int main(void)
{
    outp(0xF5, 2);
    outp(0xF6, 100);
    return 0;
}
```

This writes 100 into register 2 of the AY sound chip: port `$F5` selects the register and `$F6` takes the value. (`sound(2, 100)` does the same.)

**Notes.**

* The whole 16-bit *port* number is used as the address. Leap-C does not check it. Writing to a port that something else depends on can upset the machine.
* `border`, `sound` and `mode` are safer ways to do what most `outp` calls are for.

**Errors.** None.

**See also** `inp`, `sound`, `border`.

---

## over

`void over(int n)` -- **function**

Switches over mode on (*n* odd) or off (*n* even). In over mode, printing and plotting do not replace what is on the screen: they combine with it by **exclusive-or**. Printing a character twice in the same place therefore erases it, and so does plotting a pixel or drawing a line twice.

```c
// expect: exit 0
// screen: 0 A C
int main(void)
{
    cls();
    print("ABC");
    over(1);
    at(0, 1);
    print("B");
    over(0);
    return 0;
}
```

The second `B` is exclusive-or'd on top of the first, which clears it.

**Notes.**

* Only the low bit of *n* counts.
* Over mode applies to `print`, `puts`, `putchar`, `printf`, `plot` and `draw`.
* Use it to move something about the screen without a background: draw it, then draw it again in the same place to erase it.

```c
// expect: exit 0
// pixel: 7 7 0
// pixel: 60 70 0
int main(void)
{
    cls();
    over(1);
    plot(7, 7);
    if (!point(7, 7)) return 1;
    plot(7, 7);
    if (point(7, 7)) return 2;
    draw(50, 70, 70, 70);
    draw(50, 70, 70, 70);
    return point(60, 70);
}
```

**Errors.** None.

**See also** `inverse`, `plot`, `draw`.

---

## paper

`void paper(int n)` -- **function**

Sets the paper colour (the background of a character cell) for everything printed, plotted or drawn from now on, and for the cells `cls()` paints. The colours are 0 black, 1 blue, 2 red, 3 magenta, 4 green, 5 cyan, 6 yellow, 7 white.

```c
// expect: exit 0
// screen: 0 P
// attr: 0 0 0x17
// attr: 12 12 0x17
int main(void)
{
    paper(2);
    ink(7);
    cls();
    print("P");
    return 0;
}
```

White on red: paper 2 is 2 * 8 = 16 and ink 7 makes 23 (`0x17`) in every cell.

**Notes.**

* Only the low three bits of *n* count.
* Paper is bits 3 to 5 of a cell's attribute byte.

**Errors.** None.

**See also** `ink`, `bright`, `flash`, `border`, `cls`.

---

## pause

`void pause(unsigned n)` -- **function**

Waits for *n* display frames (1/60 second each on a TS2068, 1/50 on ZEsarUX) and then goes on. `pause(0)` returns at once.

```c
// expect: exit 1
// screen: 0 done
int main(void)
{
    unsigned t0, t1;
    cls();
    t0 = frames();
    pause(25);
    t1 = frames();
    print("done");
    return t1 - t0 - 25 < 2;
}
```

**Notes.**

* *n* may be up to 65535, about 18 minutes.
* BREAK stops the program while it waits.
* A wait of *n* frames is *n* or *n* + 1 frames as `frames()` counts them, depending on where in a frame the wait begins.

**Errors.** None.

**See also** `frames`, `beep`, `inkey`, the concept [Time](05_concepts.md#time).

---

## plot

`void plot(int x, int y)` -- **function**

Sets the pixel at *x* (0 to 255, from the left) and *y* (0 to 191, from the **top**). The pixel is drawn in the current ink, and the character cell that holds it takes the current ink, paper, bright and flash.

```c
// expect: exit 10
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 100 50 1
// pixel: 101 50 0
// attr: 6 12 0x3A
int main(void)
{
    cls();
    ink(2);
    plot(0, 0);
    plot(255, 191);
    plot(100, 50);
    plot(300, 50);
    return point(100, 50) * 10 + point(101, 50);
}
```

The pixel at (100, 50) is in the cell at row 6, column 12 (100 / 8, 50 / 8), which becomes red ink on white paper: 56 + 2 = 58 (`0x3A`). `plot(300, 50)` is off the screen and does nothing.

**Notes.**

* A pixel off the screen is ignored: no error.
* With `over(1)` the pixel is exclusive-or'd, so plotting it again clears it.
* Plotting changes the whole cell's colours: two pixels of different ink in the same 8 by 8 cell cannot both keep their colour. This is the TS2068's attribute scheme.

**Errors.** None.

**See also** `point`, `draw`, `over`, `inverse`, the concept [Screen](05_concepts.md#screen).

---

## point

`int point(int x, int y)` -- **function**

1 if the pixel at *x* (0 to 255) and *y* (0 to 191, from the top) is set, otherwise 0.

```c
// expect: exit 1
// screen: 0 1 0 0
int main(void)
{
    cls();
    plot(20, 30);
    printf("%d %d %d", point(20, 30), point(21, 30), point(-1, 30));
    return point(20, 30);
}
```

**Notes.**

* A pixel off the screen is 0, not an error.
* `point` tells whether the pixel is set, whatever its colour.

**Errors.** None.

**See also** `plot`, `attr`, `draw`.

---

## print

`void print(const char *s)` -- **function**

Prints the string *s* at the print position. It does not add a new line: the position is left just after the last character. A `'\n'` inside the string starts a new row.

```c
// expect: exit 0
// screen: 0 onetwo
// screen: 1 three
int main(void)
{
    cls();
    print("one");
    print("two");
    print("\nthree");
    return 0;
}
```

**Notes.**

* `print` is not standard C. It is the quickest way to print a fixed string, since it does no formatting: a `%` in *s* is just a `%`.
* Text wraps at column 31 and the screen scrolls when printing goes below row 23. See the start of this part.
* The text is printed in the current colours (`ink`, `paper`, `bright`, `flash`, `inverse`, `over`).

**Errors.** None.

**See also** `puts`, `putchar`, `printf`, `at`.

---

## printf

`int printf(const char *fmt, ...)` -- **function**

Prints the string *fmt*, replacing each **conversion** in it (a `%` and what follows) with the next of the arguments, in order. All other characters, `'\n'` included, are printed as they are. `printf` is the one library function that takes any number of arguments, and the compiler does not check them against the format: *the conversions and the arguments must agree*.

The conversions:

| Conversion | The argument is | Printed as |
|---|---|---|
| `%d` | `int` | a signed decimal number: `-32768` to `32767` |
| `%u` | `unsigned` (or `int`) | an unsigned decimal number: `0` to `65535` |
| `%x` | `unsigned` (or `int`) | unsigned hexadecimal, **lowercase**, without leading zeros: `0` to `ffff` |
| `%c` | `int` or `char` | the one character with that code |
| `%s` | `char *` | the characters of the string, up to its NUL |
| `%f` | `float` or `double` | a floating-point number with 6 decimal places |
| `%.Nf` | `float` or `double` | the same with *N* decimal places, *N* from 0 to 9 |
| `%%` | none | a single `%` |

A **width** may be written between the `%` and the letter: a decimal number such as `%5d`, `%3s`, `%8.2f`. The text is **right-aligned** in that many columns, padded on the left with spaces. A text longer than its width is printed whole, and a width of 0 does nothing.

```c
// expect: exit 0
// screen: 0 -7 32767
// screen: 1 65535 ff
// screen: 2 OK ok
// screen: 3 [   42][ ab][ z]
// screen: 4 100%
// screen: 5 2.500000 3.14 3
// screen: 6 3.5
int main(void)
{
    int n = 7;
    cls();
    printf("%d %d\n", -7, 32767);
    printf("%u %x\n", 65535, 255);
    printf("%c%c %s\n", 'O', 'K', "ok");
    printf("[%5d][%3s][%2c]\n", 42, "ab", 'z');
    printf("100%%\n");
    printf("%f %.2f %.0f\n", 2.5, 3.14159, 2.5);
    printf("%.1f", n / 2.0);
    return 0;
}
```

**Notes.**

* **`%f` needs a float.** An `int` argument is not converted for you: write `n / 2.0`, or `(float)n`, as above. Integer arguments go with `%d`, `%u`, `%x` and `%c`. (A `char` or `int` argument is passed as an `int`.)
* `%f` rounds half up (`%.0f` of 2.5 is `3`) and prints **every** digit before the point; a negative number has its `-`. A precision above 9 counts as 9. There is no `%e` or `%g`. See the concept [Floating point](05_concepts.md#floating-point).
* `%x` and `%u` show a negative `int` as the unsigned number with the same bits: `printf("%x", -1)` prints `ffff`.
* **Not supported:** the flags `-`, `0`, `+`, space and `#` (in `"%-3d"` the `-` is taken as the conversion character, see below), the `l` and `h` size letters, `*` for a width, `%e`, `%g`, `%o`, `%i`, `%p`, `%n`.
* **A conversion letter that printf does not know prints the next argument as a character**, and uses up that argument. `printf("%q", 65)` prints `A`.
* **The value of `printf` is undefined.** Standard C returns the number of characters printed; Leap-C's `printf` returns something you must not rely on.
* Everything is printed at the print position, in the current colours, with wrapping and scrolling as described at the start of this part. Use `at` and `tab` to place the text.
* Giving fewer arguments than conversions is not detected: the result is meaningless.

**Errors.** None.

**See also** `print`, `puts`, `putchar`, `itoa`, `at`, the concept [Floating point](05_concepts.md#floating-point).

---

## putchar

`int putchar(int c)` -- **function**

Prints the one character whose code is *c*, at the print position, and returns *c*. The code 10 (`'\n'`) moves to the start of the next row.

```c
// expect: exit 33
// screen: 0 Hi
// screen: 1 A!
int main(void)
{
    cls();
    putchar('H');
    putchar('i');
    putchar('\n');
    putchar(65);
    return putchar('!');
}
```

**Block graphics.** The codes 128 to 143 are the sixteen block graphics: each cell is divided into four quarters, and the low four bits of the code say which quarters are set. Bit 0 is the top right, bit 1 the top left, bit 2 the bottom right and bit 3 the bottom left. So 129 is the top-right quarter, 142 is everything but the top right, and 143 is a solid block.

```c
// expect: exit 142
// pixel: 4 0 1
// pixel: 0 0 0
// pixel: 4 4 0
// pixel: 8 0 1
// pixel: 12 0 0
// pixel: 12 4 1
// pixel: 8 4 1
int main(void)
{
    cls();
    putchar(129);
    return putchar(142);
}
```

The first character is the top-right quarter of its cell, pixels 4 to 7 of the top four rows. The second, in the next cell, has the top-left, bottom-right and bottom-left quarters.

**Notes.**

* The codes 144 to 164 are user-defined graphics: eight bytes each, from `$F180`. They are blank until a program stores pixels there.
* A code with no picture (for instance 127, or a code above 164) is shown as a space.
* Only the low 8 bits of *c* are printed.

**Errors.** None.

**See also** `print`, `puts`, `printf`, `at`, `getkey`, the concept [Characters](05_concepts.md#characters).

---

## puts

`int puts(const char *s)` -- **function**

Prints the string *s* at the print position and then moves to the start of the next row. It returns 10, a non-negative number.

```c
// expect: exit 10
// screen: 0 one
// screen: 1 two
// screen: 2 three
int main(void)
{
    int r;
    cls();
    puts("one");
    puts("two");
    r = puts("three");
    return r;
}
```

**Notes.**

* `puts(s)` is the same as `print(s)` followed by `putchar('\n')`.
* Printing on the bottom row scrolls the screen up one row.

**Errors.** None.

**See also** `print`, `putchar`, `printf`.

---

## rand

`int rand(void)` -- **function**

The next number of a sequence of pseudo-random numbers, from 0 to 32767. The numbers come from a fixed sequence, so a program gives the same numbers on every run; `srand` starts the sequence at a place of your choice.

```c
// expect: exit 0
// screen: 0 385 24609 27033
int main(void)
{
    int a, b, c;
    a = rand();
    b = rand();
    c = rand();
    cls();
    printf("%d %d %d", a, b, c);
    return 0;
}
```

A program that has not called `srand` gets the sequence that `srand(1)` starts: 385, 24609, 27033, 11787, 13726, ...

To throw a die, take the remainder:

```c
// expect: exit 1
// screen: 0 dice ok
int main(void)
{
    int i, n, ok = 1;
    srand(7);
    for (i = 0; i < 50; i++) {
        n = rand() % 6 + 1;
        if (n < 1 || n > 6)
            ok = 0;
    }
    cls();
    print(ok ? "dice ok" : "dice bad");
    return ok;
}
```

**Notes.**

* The largest value is 32767; the result is never negative. `rand() % n` gives 0 to *n* - 1 for *n* up to 32767.
* The generator is a 16-bit shift-and-exclusive-or generator that goes through all 65535 non-zero states before it repeats.
* To get different numbers each run, give `srand` something that changes: for instance the value of `frames()` when the user presses a key.
* In C the order in which the arguments of a call are evaluated is not defined, so call `rand` in separate statements, as above, when the order of the numbers matters.

**Errors.** None.

**See also** `srand`, `frames`, `abs`.

---

## sound

`void sound(int reg, int value)` -- **function**

Writes *value* into register *reg* of the AY-3-8912 sound chip. The registers are numbered 0 to 15, as in the chip's data sheet: 0 to 5 are the tone periods of channels A, B and C, 6 the noise period, 7 the mixer, 8 to 10 the volumes, 11 to 13 the envelope. Use this for music on more than one channel, for noise and for envelopes; `beep` is simpler for a single note.

```c
// expect: exit 0
// ay: 0=254 1=0 7=62 8=0
int main(void)
{
    sound(7, 0x3E);
    sound(0, 254);
    sound(1, 0);
    sound(8, 15);
    pause(30);
    return 0;
}
```

This sounds channel A for 30 frames, half a second on a TS2068: register 7 turns the tone of channel A on and everything else off, registers 0 and 1 give the period 254, register 8 sets full volume. When the program ends, the volumes of the three channels are put back to 0, so the sound stops; the check above reads register 8 as 0 for that reason.

**Notes.**

* *reg* must be 0 to 15. Only the low 8 bits of *value* are written (`sound(2, 256 + 77)` writes 77); a register that is narrower than 8 bits keeps only what it can hold.
* The end of a program silences the three channels (registers 8 to 10 become 0); the other registers keep their values.
* `beep` plays on channel A and leaves it silent, so it undoes a note that you started with `sound(8, 15)`.

**Errors.** A *reg* below 0 or above 15 is runtime error 4, BAD ARGUMENT:

```c
// expect: rterror 4
int main(void)
{
    sound(16, 0);
    return 0;
}
```

**See also** `beep`, `outp`, the concept [Sound](05_concepts.md#sound).

---

## sprite_get

`void sprite_get(int row, int col, int w, int h, void *buf)` -- **function**

Copies a rectangle of the screen into memory: *w* cells wide and *h* cells high, whose top-left cell is at *row* and *col*. The buffer *buf* must hold *w* * *h* * 9 bytes: for each cell, its 8 rows of pixels and then its attribute byte, the cells taken row by row. The sprite is a copy of the *screen* -- pixels and colours both.

Put it back with `sprite_put`, at the same place or at any other.

```c
// expect: exit 0
// screen: 10 AB
// screen: 11 CD
// screen: 20                               AB
// screen: 21                               CD
// attr: 10 0 0x0A
// attr: 20 30 0x0A
// attr: 5 5 0x38
char buf[36];
int main(void)
{
    cls();
    ink(2);
    paper(1);
    print("AB\nCD");
    sprite_get(0, 0, 2, 2, buf);
    ink(0);
    paper(7);
    cls();
    sprite_put(10, 0, 2, 2, buf);
    sprite_put(20, 30, 2, 2, buf);
    return 0;
}
```

The 2 by 2 cells holding the red-on-blue `AB` and `CD` are copied into `buf` (4 cells * 9 bytes = 36) and then put on the cleared screen in two places, colours and all.

**Notes.**

* A rectangle that is not wholly on the screen (rows 0 to 23, columns 0 to 31), or that is empty (*w* or *h* below 1), stops the program with runtime error 4.
* The sprite contains whatever is in the cells, including text and any pixel you have drawn there.

**Errors.** See Notes.

```c
// expect: rterror 4
char buf[90];
int main(void)
{
    sprite_get(22, 31, 1, 3, buf);
    return 0;
}
```

**See also** `sprite_put`, `attr`, `at`, the concept [Screen](05_concepts.md#screen).

---

## sprite_put

`void sprite_put(int row, int col, int w, int h, void *buf)` -- **function**

Copies the rectangle of cells that `sprite_get` saved in *buf* back onto the screen, with its top-left cell at *row* and *col*: pixels and attributes, replacing what was there. The *w* and *h* must be the same as when it was saved. The example for `sprite_get` shows both.

**Notes.**

* The rectangle must lie wholly on the screen and must not be empty: otherwise runtime error 4, BAD ARGUMENT. A negative *w* or *h* is also error 4.
* `sprite_put` puts back the attributes that were saved, not the current print colours.
* A buffer may come from anywhere, not only `sprite_get`: eight bytes of pixels then one attribute byte for each cell.

**Errors.** See Notes.

**See also** `sprite_get`, `plot`, `attr`.

---

## srand

`void srand(unsigned seed)` -- **function**

Restarts the sequence of `rand` at the place named by *seed*. The same *seed* always gives the same sequence.

```c
// expect: exit 0
// screen: 0 385 385
int main(void)
{
    int a, b;
    cls();
    srand(1);
    a = rand();
    srand(0);
    b = rand();
    printf("%d %d", a, b);
    return 0;
}
```

**Notes.**

* The seeds 0 and 1 give the same sequence (the generator's state may not be 0).
* A program that never calls `srand` gets the sequence of `srand(1)`, every run.

**Errors.** None.

**See also** `rand`, `frames`.

---

## strcat

`char *strcat(char *d, const char *s)` -- **function**

Appends the string *s* to the end of the string *d* (the NUL at the end of *d* is overwritten by the first character of *s*, and a NUL is put at the new end). Returns *d*.

```c
// expect: exit 7
// screen: 0 Leap-C
char s[20];
int main(void)
{
    cls();
    strcpy(s, "Leap");
    strcat(s, "-C");
    puts(s);
    return strlen(strcat(s, "!"));
}
```

**Notes.**

* *d* must already hold a string (end with a NUL) and have room for both. Nothing is checked.
* `strcat(d, "")` leaves *d* as it was.

**Errors.** None.

**See also** `strcpy`, `strlen`, `strncpy`.

---

## strchr

`char *strchr(const char *s, int c)` -- **function**

Finds the first place in the string *s* where the character *c* occurs, and returns a pointer to it; or 0 if it does not occur. *c* may be 0, in which case the result points to the NUL that ends *s*.

```c
// expect: exit 12
// screen: 0 o, world|4
// screen: 1 1
char s[20] = "hello, world";
int main(void)
{
    char *p;
    cls();
    p = strchr(s, 'o');
    printf("%s|%d\n", p, p - s);
    printf("%d", strchr(s, 'z') == 0);
    return strchr(s, 0) - s;
}
```

`p - s` is the position of the character in the string, counting from 0.

**Notes.**

* Only the low 8 bits of *c* are compared.
* To find the next one, search again from `p + 1`.

**Errors.** None.

**See also** `strcmp`, `strlen`, the concept [Strings](05_concepts.md#strings).

---

## strcmp

`int strcmp(const char *a, const char *b)` -- **function**

Compares the strings *a* and *b* character by character. The result is negative if *a* comes before *b*, positive if it comes after, and 0 if the strings are equal. The characters are compared as unsigned numbers (their codes, so `"Z"` comes before `"a"`), and a string that is a leading part of another comes before it.

```c
// expect: exit 1
// screen: 0 1 0 1 1
int main(void)
{
    cls();
    printf("%d %d %d %d", strcmp("abc", "abd") < 0,
                          strcmp("abc", "abc"),
                          strcmp("b", "a") > 0,
                          strcmp("Z", "a") < 0);
    return strcmp("ab", "abc") < 0;
}
```

**Notes.**

* Test the sign of the result (`< 0`, `== 0`, `> 0`), not a particular value. Use `strcmp(a, b) == 0`, not `a == b`, to ask whether two strings are equal: `==` compares the two pointers.
* Capital and small letters are different: `strcmp("A", "a")` is not 0.

**Errors.** None.

**See also** `memcmp`, `strchr`, the concept [Strings](05_concepts.md#strings).

---

## strcpy

`char *strcpy(char *d, const char *s)` -- **function**

Copies the string *s*, with its NUL, to the memory at *d*, and returns *d*.

```c
// expect: exit 4
// screen: 0 copy
char d[10];
int main(void)
{
    cls();
    strcpy(d, "copy");
    puts(d);
    return strlen(strcpy(d, "four"));
}
```

**Notes.**

* *d* must have room for the whole of *s* and its NUL. Nothing is checked: a string that is too long overwrites whatever follows the array.
* Strings that overlap give undefined results.
* Use `strncpy` to limit the number of characters copied.

**Errors.** None.

**See also** `strncpy`, `strcat`, `memcpy`, the concept [Strings](05_concepts.md#strings).

---

## strlen

`unsigned strlen(const char *s)` -- **function**

The number of characters in the string *s*, not counting the NUL that ends it.

```c
// expect: exit 10
// screen: 0 0 6
int main(void)
{
    cls();
    printf("%u %u", strlen(""), strlen("Leap-C"));
    return strlen("0123456789");
}
```

**Notes.**

* The result is `unsigned`. `strlen(a) - strlen(b)` is never negative: if *b* is longer the difference is a large number. Compare the lengths instead.
* `sizeof` of an array is its size; `strlen` is the length of the string it holds now.

**Errors.** None.

**See also** `strcpy`, `strcat`, `strchr`.

---

## strncpy

`char *strncpy(char *d, const char *s, unsigned n)` -- **function**

Copies at most *n* characters of the string *s* to *d*, and returns *d*. If *s* is shorter than *n*, the rest of the *n* bytes at *d* are filled with NULs.

```c
// expect: exit 120
// screen: 0 abcde
// screen: 1 0 0 #
int main(void)
{
    char d[6];
    cls();
    strncpy(d, "abcdefgh", 5);
    d[5] = 0;
    puts(d);
    memset(d, '#', 5);
    d[5] = 0;
    strncpy(d, "xy", 4);
    printf("%d %d %c", d[2], d[3], d[4]);
    return d[0];
}
```

**Notes.**

* **If *s* has *n* or more characters, no NUL is stored.** The first call above copies five letters and the program puts the NUL in itself. A string made with `strncpy` is not always a string until you finish it.
* With *n* equal to 0 nothing is copied.
* `strncpy` fills exactly *n* bytes, so *d* needs room for *n*, even when *s* is short.

**Errors.** None.

**See also** `strcpy`, `strcat`, `memset`.

---

## tab

`void tab(int col)` -- **function**

Moves the print position to column *col* of the **current** row. The row is not changed.

```c
// expect: exit 0
// screen: 0 A  C      B
int main(void)
{
    cls();
    print("A");
    tab(10);
    print("B");
    tab(35);
    print("C");
    return 0;
}
```

`tab(35)` is column 3: *col* is taken modulo 32. `C` is printed there, between `A` and `B`, without disturbing them.

**Notes.**

* `tab` only moves the position; it does not clear what it passes over.
* Use `at` to set the row as well.

**Errors.** None.

**See also** `at`, `print`, `printf`.

---

## tape_load

`int tape_load(const char *name, void *addr, unsigned max)` -- **function**

Loads a **data tape** that `tape_save` wrote: it waits for the next data tape called *name* (the empty string `""` accepts any name) and stores its bytes from the address *addr*, at most *max* of them. It returns the number of bytes loaded, or a negative number if it failed:

| Result | Meaning |
|---|---|
| 0 or more | the length of the data, which is now at *addr* |
| -1 | nothing was loaded: no such tape within about 2 minutes, or a tape longer than *max*, or a bad block before the data. *addr* is untouched. |
| -2 | the data block failed after part of it had been stored at *addr* |
| -3 | the tape is not a Leap-C tape (its version word is not Leap-C's); nothing was stored |

Start the tape playing before the call or just after it: `tape_load` waits. See [Tapes](05_concepts.md#tapes), and [EMULATORS.md](../EMULATORS.md) for how to play a tape in an emulator.

```c
char buf[100];
int main(void)
{
    int n;
    cls();
    print("Play the tape...");
    n = tape_load("mydata", buf, 100);
    if (n < 0) {
        printf("\nfailed: %d", n);
        return n;
    }
    printf("\nloaded %d bytes", n);
    return 0;
}
```

(This example is not run by the build, which has no tape to play.)

**Notes.**

* A program's own tape (`SAVE`, `LOAD`) and a data tape are different kinds: `tape_load` skips program tapes, and `LOAD` skips data tapes. Leap-C's tapes carry their own version word, so the TS2068's BASIC and Leap V2 refuse them and Leap-C refuses theirs.
* *addr* can be any address in RAM.
* BREAK, or SPACE, during the transfer stops it and ends the program with runtime error 5, shown as `BREAK`.
* While a block of the tape moves, interrupts are off, so `frames()` does not count.

**Errors.**

| Mistake | What happens |
|---|---|
| a *name* longer than 10 characters | runtime error 4, BAD ARGUMENT |
| BREAK or SPACE pressed | runtime error 5 (shown as `BREAK`) |

```c
// expect: rterror 4
char buf[4];
int main(void)
{
    tape_load("a_long_file_name", buf, 4);
    return 0;
}
```

**See also** `tape_save`, the concept [Tapes](05_concepts.md#tapes).

---

## tape_save

`void tape_save(const char *name, const void *addr, unsigned len)` -- **function**

Writes *len* bytes, starting at the address *addr*, to the tape as a **data tape** called *name*. *name* is a string of 1 to 10 characters. The function returns when both blocks of the tape (a header and the data) have been sent: about 7 seconds, plus 5 to 7 milliseconds for every byte.

Start the recorder before the call. Read the data back with `tape_load`.

```c
char data[8] = "Leap-C";
int main(void)
{
    cls();
    print("Record...");
    tape_save("mydata", data, 7);
    print("saved");
    return 0;
}
```

(This example is not run by the build, which has no tape to play.)

**Notes.**

* The data can be anything: text, an array, a structure. It is saved as bytes; `tape_load` puts the same bytes back, wherever you say.
* *addr* can be any address in RAM.
* BREAK, or SPACE, during the transfer stops it and ends the program with runtime error 5, shown as `BREAK`.
* While a block of the tape moves, interrupts are off, so `frames()` does not count.

**Errors.**

| Mistake | What happens |
|---|---|
| an empty *name*, or one longer than 10 characters | runtime error 4, BAD ARGUMENT |
| *len* is 0 | runtime error 4, BAD ARGUMENT |
| BREAK or SPACE pressed | runtime error 5 (shown as `BREAK`) |

```c
// expect: rterror 4
char data[4];
int main(void)
{
    tape_save("a_long_file_name", data, sizeof data);
    return 0;
}
```

**See also** `tape_load`, the concept [Tapes](05_concepts.md#tapes), [Appendix C](08_appendices.md#appendix-c-runtime-errors).
