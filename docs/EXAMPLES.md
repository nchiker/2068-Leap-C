# Leap-C by example

**Phase 8, 2026-10-21.** Short programs showing the Release 1 language (`spec.md` §4) and library (`spec.md` §7). **Every example here is a test.** `tools/docexamples.py` copies each one to `tests/doc/`, and `make test` compiles and runs it on the production ROM: directly, through the shell's `RUN`, and under the RAM canary. `make check` fails if `tests/doc/` falls out of step with this file.

The `//` lines at the top of an example are its checked results; the rest of the program ignores them:

| Line | Meaning |
|---|---|
| `// expect: exit N` | `main` returns N: the exit status the shell shows |
| `// expect: rterror N` | the program stops with runtime error N (`spec.md` §5.9) |
| `// expect: error E_NAME L` | the compile stops with that error at line L (the lines of the example) |
| `// screen: R TEXT` | text row R (0-23) reads TEXT |
| `// attr: R C V`, `// pixel: X Y V`, `// ay: REG=V` | a cell's attribute, a pixel (from the top left), an AY register |
| `// keys: ...` | the keys typed while the program reads the keyboard |
| `// library: NAME` | (Phase 10) the library NAME is loaded first, as `LIB "NAME"` loads it (`spec.md` §7.2) |

Programs start with `cls()` when they print, because the screen holds whatever was there before.

## 1. A first program

`main` returns the program's exit status. `printf` and the rest of the library need no `#include` (`<leap.h>` is accepted and built in).

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

## 2. Integers

`int` and `unsigned` are 16 bits and wrap around. `char` is unsigned; `signed char` sign-extends. Signed `/` truncates toward zero, and `%` takes the dividend's sign.

```c
// expect: exit 0
// screen: 0 255 -1 -32768 65535
// screen: 1 -3 -1 3 1
int main(void)
{
    char c = 255;
    signed char s = 255;
    int big = 32767;
    unsigned u = 0;
    cls();
    printf("%d %d %d %u\n", c, s, big + 1, u - 1);
    printf("%d %d %d %d\n", -7 / 2, -7 % 2, 7 / 2, 7 % 2);
    return 0;
}
```

## 3. Functions and recursion

Prototypes are optional, and a function may be called before its definition.

```c
// expect: exit 120
int fact(int n);
int main(void)
{
    return fact(5);
}
int fact(int n)
{
    return n <= 1 ? 1 : n * fact(n - 1);
}
```

## 4. Arrays, pointers and strings

```c
// expect: exit 0
// screen: 0 sum 15, max 5
// screen: 1 Leap-C: 6 characters
int a[5] = { 1, 2, 3, 4, 5 };
char name[16];
int sum(int *p, int n)
{
    int s = 0;
    while (n--)
        s += *p++;
    return s;
}
int main(void)
{
    int i, max = a[0];
    for (i = 1; i < 5; i++)
        if (a[i] > max)
            max = a[i];
    cls();
    printf("sum %d, max %d\n", sum(a, 5), max);
    strcpy(name, "Leap");
    strcat(name, "-C");
    printf("%s: %d characters\n", name, strlen(name));
    return strcmp(name, "Leap-C");
}
```

## 5. Structures, enumerations, pointers to functions and the heap

```c
// expect: exit 0
// screen: 0 3 2 1
// screen: 1 add 7, sub 3
typedef struct node { int v; struct node *next; } Node;
enum op { ADD, SUB };
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int (*ops[])(int, int) = { add, sub };
int main(void)
{
    Node *list = 0, *n;
    int i;
    cls();
    for (i = 1; i <= 3; i++) {
        n = malloc(sizeof(Node));
        if (!n)
            return 1;
        n->v = i;
        n->next = list;
        list = n;
    }
    for (n = list; n; n = n->next)
        printf("%d ", n->v);
    printf("\nadd %d, sub %d\n", ops[ADD](5, 2), ops[SUB](5, 2));
    while (list) {
        n = list->next;
        free(list);
        list = n;
    }
    return 0;
}
```

## 6. Initialisers

Static objects take constant initialisers: nested braces may be left out (brace elision), a `char` array may come from a string, and what a list leaves out is zero. An automatic scalar takes any expression, in braces or not. Automatic arrays and structures cannot have initialisers in Release 1: make them `static`.

```c
// expect: exit 0
// screen: 0 Jan 31
// screen: 1 Feb 28
// screen: 2 Mar 31
// screen: 3 4 0 6
struct month { char name[4]; int days; } months[] = { "Jan", 31, "Feb", 28, { "Mar", 31 } };
int grid[2][3] = { { 1, 2 }, 3, 4 };
int main(void)
{
    int i, k = { 6 };
    static char *unused[2] = { "x" };
    cls();
    for (i = 0; i < sizeof months / sizeof months[0]; i++)
        printf("%s %d\n", months[i].name, months[i].days);
    printf("%d %d %d\n", grid[1][1], grid[0][2], k);
    return unused[1] != 0;
}
```

## 7. The preprocessor

Object-like macros; `#include <leap.h>` is accepted and does nothing (the library is built in).

```c
// expect: exit 0
// screen: 0 area 300
#include <leap.h>
#define W 20
#define H 15
#define AREA (W * H)
int main(void)
{
    cls();
    printf("area %d\n", AREA);
    return 0;
}
```

## 8. Floating point

`float` and `double` are the same type: the Sinclair 5-byte format (a 32-bit mantissa: about 9.6 significant digits; magnitudes up to about 1.7E38). Integers convert to and from it as in C; a conversion to an integer truncates toward zero. `printf`'s `%f` prints 6 decimals, `%.Nf` N of them (0-9).

```c
// expect: exit 0
// screen: 0 area 78.539816
// screen: 1 1/3 = 0.333333333
// screen: 2 int 7, back 7.00
float area(float r)
{
    return 3.14159265 * r * r;
}
int main(void)
{
    float third = 1.0 / 3;
    int n = 7.9;
    cls();
    printf("area %f\n", area(5));
    printf("1/3 = %.9f\n", third);
    printf("int %d, back %.2f\n", n, (float)n);
    return 0;
}
```

Decimal fractions such as 0.1 are not exact in binary, so test floats with a tolerance rather than `==`:

```c
// expect: exit 0
// screen: 0 1.000000000 is not 1
// screen: 1 -40.0 32.0 98.6 212.0
int main(void)
{
    float s = 0;
    int i;
    cls();
    for (i = 0; i < 10; i++)
        s += 0.1;
    if (s != 1)
        printf("%.9f is not 1\n", s);
    for (i = -40; i <= 100; i += i < 37 ? (i < 0 ? 40 : 37) : 63)
        printf("%.1f ", i * 1.8 + 32);
    return s - 1 > 1e-8;
}
```

There is no math library in Release 1; the usual functions are short in C:

```c
// expect: exit 0
// screen: 0 sqrt(2) = 1.41421356
float root(float x)
{
    float r = x;
    int i;
    for (i = 0; i < 20; i++)
        r = (r + x / r) / 2;
    return r;
}
int main(void)
{
    cls();
    printf("sqrt(2) = %.8f\n", root(2));
    return 0;
}
```

A float overflow or division by zero stops the program with runtime error 6 (in a constant expression it is a compile error, `NUMBER TOO LARGE`):

```c
// expect: rterror 6
int main(void)
{
    float zero = 0;
    return 1 / zero;
}
```

## 9. Text and colour

Rows 0-23 and columns 0-31. `at(row, col)` moves the print position and `tab(col)` the column; `ink`, `paper`, `bright`, `flash`, `inverse` and `over` set how later text is printed.

```c
// expect: exit 0
// screen: 5           MIDDLE
// screen: 6 ab    cd
// attr: 5 10 0x6A
// attr: 6 0 0x38
int main(void)
{
    cls();
    at(5, 10);
    ink(2);
    paper(5);
    bright(1);
    print("MIDDLE");
    ink(0);
    paper(7);
    bright(0);
    at(6, 0);
    print("ab");
    tab(6);
    print("cd");
    return 0;
}
```

`printf` supports `%d %u %x %c %s %f %%` and a width; text longer than the width is printed whole.

```c
// expect: exit 0
// screen: 0 [   42][ff][  A][-2.50][hi]
int main(void)
{
    cls();
    printf("[%5d][%x][%3c][%5.2f][%1s]\n", 42, 255, 'A', -2.5, "hi");
    return 0;
}
```

## 10. The keyboard

`gets(buf, max)` reads a line with editing (DELETE) and echo; `getkey()` waits for a key, `inkey()` does not (0 when none).

```c
// keys: "Leb" DELETE "ap" ENTER "y"
// expect: exit 1
// screen: 0 Name? Leap
// screen: 1 Hello, Leap!
char buf[11];
int main(void)
{
    cls();
    print("Name? ");
    gets(buf, sizeof buf);
    printf("Hello, %s!\n", buf);
    return getkey() == 'y';
}
```

## 11. Graphics

Pixels are numbered from the top left: x 0-255, y 0-191. `draw` includes both ends; `point` is 0 off the screen.

```c
// expect: exit 0
// pixel: 0 0 1
// pixel: 255 191 1
// pixel: 10 180 1
// attr: 0 0 0x3A
int main(void)
{
    cls();
    ink(2);
    draw(0, 0, 255, 191);
    plot(10, 180);
    return point(10, 180) + point(300, 5) - 1;
}
```

`sprite_get` and `sprite_put` copy a rectangle of character cells (9 bytes a cell: 8 pixel rows, then the attribute).

```c
// expect: exit 0
// screen: 0 AB
// screen: 3           AB
// attr: 3 11 0x0E
char cells[18];
int main(void)
{
    cls();
    ink(6);
    paper(1);
    print("AB");
    sprite_get(0, 0, 2, 1, cells);
    sprite_put(3, 10, 2, 1, cells);
    return cells[8] != 0x0E;
}
```

The hi-res colour mode (`mode(1)`) uses the memory at `$6000-$77FF`; `#pragma hires` keeps the program's image out of it.

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

## 12. Sound

`beep(frames, semitone)` plays a note on the AY's channel A (0 is middle C); `sound(reg, value)` writes an AY register.

```c
// expect: exit 0
// ay: 0=100 1=2
int main(void)
{
    beep(5, 0);
    sound(0, 100);
    sound(1, 2);
    return 0;
}
```

## 13. Time and random numbers

`frames()` counts display frames; `pause(n)` waits n of them. `rand()` returns 0-32767; `srand(n)` restarts its sequence.

```c
// expect: exit 0
int main(void)
{
    unsigned t = frames();
    int i, r;
    pause(3);
    if (frames() - t < 3)
        return 1;
    srand(7);
    r = rand();
    for (i = 0; i < 100; i++)
        if (rand() < 0)
            return 2;
    srand(7);
    return rand() != r;
}
```

## 14. Ports

`inp` and `outp` take 16-bit port addresses. Port `$7FFE` reads the keyboard row SPACE to B: bits 0-4 are 1 while no key is down.

```c
// expect: exit 31
int main(void)
{
    outp(0xFE, 1);
    return inp(0x7FFE) & 31;
}
```

## 15. Strings and memory

```c
// expect: exit 0
// screen: 0 hello world 11
// screen: 1 h*llo
// screen: 2 hhelloworld
char s[20], t[20];
int main(void)
{
    cls();
    strcpy(s, "hello");
    strcat(s, " world");
    printf("%s %d\n", s, strlen(s));
    memcpy(t, s, 5);
    t[5] = 0;
    *strchr(t, 'e') = '*';
    printf("%s\n", t);
    memmove(s + 1, s, 5);
    printf("%s\n", s);
    memset(t, 'x', 3);
    if (memcmp(t, "xxxlo", 5))
        return 1;
    strncpy(t, "abc", 5);
    return strcmp(t, "abc") != 0 || strcmp("a", "b") >= 0;
}
```

## 16. Conversions

```c
// expect: exit 0
// screen: 0 -42 ff 1010 zz
// screen: 1 32767 -32768
char b1[18], b2[18], b3[18];
int main(void)
{
    cls();
    printf("%d %s %s %s\n", atoi("  -42x"), itoa(255, b1, 16), itoa(10, b2, 2), itoa(1295, b3, 36));
    printf("%d %d\n", abs(-32767), abs(-32768));
    return 0;
}
```

## 17. The heap and leaving a program

`malloc` returns NULL when nothing fits (and for 32 KB or more); `free(NULL)` does nothing. `exit(n)` ends the program from any depth.

```c
// expect: exit 3
void deep(int n)
{
    if (n == 0)
        exit(3);
    deep(n - 1);
}
int main(void)
{
    char *p = malloc(1000);
    if (!p || malloc(40000))
        return 1;
    free(p);
    free(0);
    deep(10);
    return 0;
}
```

## 18. Tape

`tape_save(name, addr, len)` and `tape_load(name, addr, max)` keep data blocks on cassette. A name has 1-10 characters; anything else is runtime error 4.

```c
// expect: rterror 4
char data[4];
int main(void)
{
    tape_save("a_long_file_name", data, sizeof data);
    return 0;
}
```

## 19. Errors

A compile error names its line. The shell shows it as `ERROR 23 LINE 5` with the message `UNDECLARED IDENTIFIER` and puts the cursor on that line:

```c
// expect: error E_UNDECL 5
int main(void)
{
    int count = 0;
    return cont;
}
```

Runaway recursion stops with runtime error 1 (stack overflow) instead of overwriting memory (`noaudit` tells the harness not to stop at each of the many returns that never come):

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

## 20. A library from tape

(Phase 10.) A library adds functions from tape. `LIB "shapes"` loads the example library (`libs/shapes.asm`; its tapes are built by `make libs` and are in the hardware kit) and reports `LIBRARY shapes: 3 FUNCTIONS`. Its functions are then called like the built-in ones, with no declaration: `circle(x, y, r)`, `box(x0, y0, x1, y1)` and `isqrt(n)`. `LIB` alone unloads it; `NEW` and `LOAD` keep it.

```c
// library: shapes
// expect: exit 12
// screen: 0 ROOTS 3 10 255
// pixel: 128 76 1
// pixel: 108 96 1
int main(void)
{
    cls();
    printf("ROOTS %u %u %u", isqrt(9), isqrt(120), isqrt(65535u));
    circle(128, 96, 20);
    box(98, 66, 158, 126);
    return isqrt(150);
}
```
