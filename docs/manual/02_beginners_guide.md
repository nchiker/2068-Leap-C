# Part 2 -- Beginner's guide

This part teaches C from nothing, one small step at a time. You do not need to have programmed before. Read it with the machine in front of you (a real one, or an emulator) and type in every example. Each complete program here has been run on the Leap-C ROMs, and what appears on your screen should be exactly what is described.

Each chapter is short. If you already know C, read Chapters 1 to 3 for the editor and skim the rest; [Part 3](03_keywords.md), [Part 4](04_library.md) and [Part 5](05_concepts.md) are the reference.

The comment lines at the top of a program that begin `// expect:`, `// screen:`, `// keys:` and so on are checks for the manual's automated tests. To the compiler they are comments, so you may leave them out when you type. Their meaning is in [Part 1](01_introduction.md#how-to-read-this-manual).

## Chapter 1 -- Switching on

Switch on the machine. A short chord plays (C, E and G, one after another, just under a second), and you see a white screen with a black row at the bottom:

```
...
LINE 1/0
```

![The screen after switching on](../images/editor_start.png)

You are in the **editor**. It is where you write programs. The bottom row is the **status row**. It says `LINE 1/0`, meaning "the cursor is on line 1, and the program has 0 lines so far". The three little coloured squares at its right (red, green and blue) are decoration. The black block is the **cursor**: it shows where the next character you type will go. Everything above the status row, rows 0 to 22, is for your program and for what it prints.

There is no "OK" prompt and no copyright message. If you see something else (a blank screen, or the TS2068's own BASIC screen) the ROMs were not set up properly; the [emulator guide](../EMULATORS.md) says what to do.

There are no line numbers. A program is a list of lines, one under the other.

## Chapter 2 -- Your first program

Type the following, pressing **ENTER** at the end of each line:

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

You need some punctuation that the TS2068 has no keys for. Hold **SYMBOL SHIFT** and press a letter or digit. On a PC, SYMBOL SHIFT is **Ctrl**:

| You want | SYMBOL SHIFT and | You want | SYMBOL SHIFT and |
|---|---|---|---|
| `"` | P | `;` | O |
| `{` | F | `}` | G |
| `(` | 8 | `)` | 9 |
| `\` | D | `,` | N |

The full table is in the concept [The editor](05_concepts.md#the-editor). Indent with spaces: there is no TAB key. Capital letters come from CAPS SHIFT (Shift on a PC) and a letter. When you leave a line, its C keywords (`int`, `void`, `return`) turn **bold**; that tells you that the editor recognised them.

![The first program typed into the editor](../images/editor_first_program.png)

The program now has 8 lines (6 if you left out the `//` lines), and the cursor is on the empty line after them. That empty line after the last line of the program is the **last line**, and it is where you type **commands**. Type

```
RUN
```

and press ENTER. The status row says `COMPILING` for a moment. The machine has turned the whole program into Z80 machine code and now runs it:

![The program after RUN](../images/first_program_run.png)

```
Hello, TS2068!

...
EXIT 0
IMAGE 39 B  HEAP 18340 B
```

The greeting is the program's output. The two rows at the bottom are the **report**. `EXIT 0` is the number `main` returned. `IMAGE` is the size of the compiled program in bytes, and `HEAP` is the memory the program could take with `malloc()`. Let go of all keys, then press one: you are back in the editor with your program as you left it. (A key still held down from the command is ignored, so that a report cannot vanish before you read it.)

### What the program says

```c
int main(void)
```

Every C program is made of **functions**. This line starts one called `main`. The program begins at `main`, and its work ends when `main` ends. `int` says that `main` gives back a whole number when it is done, and `void` that it needs nothing to be handed to it.

```c
{
```

and the `}` at the end are **braces**. They enclose the **body** of the function: the statements it carries out, one after another, from the top.

```c
    cls();
```

A **statement** is one instruction, and it ends with a **semicolon**. `cls()` is a call to a **library function** that clears the screen. Here the function has nothing to be told, so its brackets are empty. A program starts with the screen as the editor left it, so a program that prints should call `cls()` first.

```c
    printf("Hello, TS2068!\n");
```

`printf` prints. What is between the double quotes is a **string**: text. The two characters `\n` are a special code that means "start a new line". Without it the next thing printed would follow on the same row.

```c
    return 0;
```

`return` ends the function and hands back a value. For `main` that value is the `EXIT` report.

You do not need to write `#include` for the library. `printf` and the rest are built into the ROM. (`#include <leap.h>` is accepted and does nothing.)

C is **case-sensitive**: `Main` or `PRINTF` would not be understood.

### More than one line of output

```c
// expect: exit 0
// screen: 0 Hello!
// screen: 1 I am a Timex Sinclair 2068.
// screen: 2 I run C.
int main(void)
{
    cls();
    puts("Hello!");
    puts("I am a Timex Sinclair 2068.");
    printf("I run C.\n");
    return 0;
}
```

`puts` prints a string and then starts a new line by itself, so it needs no `\n`. See [puts](04_library.md#puts) and [printf](04_library.md#printf).

### The other commands

Four more commands are typed on the empty last line, just as `RUN` is.

| Command | Does |
|---|---|
| `LIST` | shows the program from the top, a page at a time. A key shows the next page. **BREAK** (CAPS SHIFT and SPACE together) ends it. |
| `FREE` | shows how much memory the program uses and how much is left |
| `NEW` | clears the program, so you can start another |
| `RUN` | compiles and runs |

`FREE` reports `SOURCE s B  FREE f B`: the size of the program text, and the room left for it. See [LIST](03_keywords.md#list), [FREE](03_keywords.md#free), [NEW](03_keywords.md#new) and [RUN](03_keywords.md#run).

## Chapter 3 -- Correcting mistakes

Everybody makes mistakes. You edit one line at a time: type, move with the cursor keys, and ENTER stores the line. Moving off a line with the up or down key stores it too. Characters you type go in at the cursor. Hold **CAPS SHIFT** and press:

| Keys | Effect |
|---|---|
| 5 | cursor left |
| 8 | cursor right |
| 7 | cursor up (between the rows of a wrapped line first) |
| 6 | cursor down |
| 0 (DELETE) | delete the character before the cursor; on an empty line, delete the line |
| 1 | delete the whole line |
| ENTER | insert an empty line before this one |
| SPACE (BREAK) | stop a running program, a listing or a tape command |

On a PC, the arrow keys do the cursor movements and Backspace is DELETE; the [emulator guide](../EMULATORS.md) has the whole table. (**Take care with Esc in Fuse**: it is CAPS SHIFT and 1, which deletes the line you are on.)

A line may have up to 127 characters; a long one wraps on to the next row of the screen.

### When the compiler does not understand

`RUN` looks at the whole program before it runs a single instruction. If it finds something it cannot understand, **nothing runs at all**. Suppose you forget a semicolon:

```c
// expect: error E_SYNTAX 5
int main(void)
{
    cls();
    printf("Hello\n")
    return 0;
}
```

Type that (leave out the `//` line if you like; then the missing semicolon is on line 4) and `RUN` it. You get two report rows:

```
...
ERROR 20: SYNTAX ERROR
LINE 5
```

The number says which mistake it was ([Appendix B](08_appendices.md) lists them all); the line is the line of the program, counted from 1. Press a key. The editor shows the program with the cursor **at the place where the compiler stopped**: here, at the end of the line that lacks the semicolon. Type `;`, and press ENTER. Then move down with CAPS SHIFT and 6 until you reach the empty last line (the status row shows `LINE 8/7`: the first number is one more than the second), and `RUN` again.

You cannot do damage by making a mistake. The worst that happens is a message. Compile errors are explained in Chapter 18, and in the concept [Errors](05_concepts.md#errors).

## Chapter 4 -- Numbers

C does arithmetic on whole numbers with `+ - * /`, and `%` for the remainder after a division. Multiplication, division and remainder are done before addition and subtraction; use brackets to change that.

```c
// expect: exit 0
// screen: 0 5 6 42 5
// screen: 1 14 20
// screen: 2 3 1
int main(void)
{
    cls();
    printf("%d %d %d %d\n", 2 + 3, 10 - 4, 6 * 7, 20 / 4);
    printf("%d %d\n", 2 + 3 * 4, (2 + 3) * 4);
    printf("%d %d\n", 7 / 2, 7 % 2);
    return 0;
}
```

Look at `printf` now. In its string, `%d` means "put a whole number here"; the numbers after the string fill the `%d`s in order. This is how you print a number. The last line shows that dividing whole numbers gives a whole number: `7 / 2` is 3, and the remainder, `7 % 2`, is 1. The fraction is dropped. (Chapter 16 has numbers with fractions.)

### Variables

To remember a number for later, give it a name. You must first **declare** it, saying what **type** it is. A named place that holds a number is a **variable**, and `int` is the type of whole numbers:

```c
// expect: exit 36
// screen: 0 total 36
int main(void)
{
    int price = 12;
    int quantity = 3;
    int total;
    total = price * quantity;
    cls();
    printf("total %d\n", total);
    return total;
}
```

Declarations come first in the function, before any other statement. `int price = 12;` declares `price` and gives it a first value. `int total;` declares it with no value yet; its first value is the result of `total = price * quantity;`. Always give a variable a value before you use it.

The `=` is **assignment**, not a statement of equality. `score = score + 5;` does not say that something equals itself plus five, which would be silly. It says: take what `score` is now, add five, and keep that in `score`.

```c
// expect: exit 31
// screen: 0 score 31
int main(void)
{
    int score = 10;
    score = score + 5;
    score *= 2;
    score++;
    cls();
    printf("score %d\n", score);
    return score;
}
```

`score *= 2;` is short for `score = score * 2;`, and `score++;` for adding one. The other short forms are `+= -= /= %=` and `--`. A name is made of letters, digits and underscores, starts with a letter or underscore, and may be long (31 characters count). Capitals matter. You cannot use a keyword such as `int` or `while` as a name.

### How big can a number be?

An `int` is 16 bits: it holds -32768 to 32767. If you go past the end it **wraps around**, with no error. An `unsigned` is also 16 bits but holds 0 to 65535. A `char` is 8 bits and holds 0 to 255; it is mostly for characters (Chapter 5).

```c
// expect: exit 0
// screen: 0 32767 -32768
// screen: 1 255 0
// screen: 2 65535 0
int main(void)
{
    int n = 32767;
    char c = 255;
    unsigned u = 65535;
    cls();
    printf("%d ", n);
    n = n + 1;
    printf("%d\n", n);
    printf("%d ", c);
    c = c + 1;
    printf("%d\n", c);
    printf("%u ", u);
    u = u + 1;
    printf("%u\n", u);
    return 0;
}
```

`%u` prints an `unsigned` number, and `%x` prints a number in hexadecimal. See [printf](04_library.md#printf) and the concept [Memory](05_concepts.md#memory).

## Chapter 5 -- Characters and strings

A letter in single quotes is a **character constant**. It is a number: the character's code.

```c
// expect: exit 65
// screen: 0 A 65 B
int main(void)
{
    char c = 'A';
    cls();
    printf("%c %d %c\n", c, c, c + 1);
    return c;
}
```

`%c` prints a number as the character with that code, and `%d` as a number. So `'A'` is 65, and one more is 66, which is `B`. The codes are ASCII; Appendix D has the table.

A **string** is a row of characters that ends with a zero, the character `\0`, which marks the end. A string in double quotes, such as `"Leap"`, is stored like that for you. To keep a string that you change, make an **array** of `char` (arrays are Chapter 9) with room for the longest string and its zero. The library has functions for strings: `strcpy` copies, `strcat` joins on to the end, `strlen` counts.

```c
// expect: exit 13
// screen: 0 Leap-C is fun
// screen: 1 length 13, first L
char text[30];
int main(void)
{
    strcpy(text, "Leap-C");
    strcat(text, " is fun");
    cls();
    printf("%s\n", text);
    printf("length %d, first %c\n", strlen(text), text[0]);
    return strlen(text);
}
```

`%s` prints a string. `text[0]` is the first character of `text`: counting starts from **zero**. This array is declared before `main`, outside any function, so it is a **global**: any function can use it. A string you only read can be named by a pointer: `char *who = "world";` (Chapter 10).

Some other characters need a **backslash** code inside quotes: `\n` new line, `\"` a double quote, `\\` a backslash, `\t` a tab, `\0` zero. See [strcpy](04_library.md#strcpy), [strcat](04_library.md#strcat), [strlen](04_library.md#strlen) and [putchar](04_library.md#putchar).

## Chapter 6 -- Making decisions

A program must be able to choose. `if` carries out a statement only when its **condition** is true. A condition compares two things:

| Comparison | Means |
|---|---|
| `a == b` | equal |
| `a != b` | not equal |
| `a < b`, `a > b` | less, greater |
| `a <= b`, `a >= b` | less or equal, greater or equal |

C has no special true and false. A comparison is **1** when true and **0** when false, and any number that is not zero counts as true. `&&` means "and", `||` means "or", `!` means "not".

```c
// expect: exit 1
// screen: 0 Merit
// screen: 1 middle band
// screen: 2 exactly 72
int main(void)
{
    int mark = 72;
    cls();
    if (mark >= 80)
        puts("Distinction");
    else if (mark >= 60)
        puts("Merit");
    else if (mark >= 40)
        puts("Pass");
    else
        puts("Fail");
    if (mark > 50 && mark < 90)
        puts("middle band");
    if (mark == 72)
        puts("exactly 72");
    return mark > 50;
}
```

The `else` part is optional; it runs when the condition was false. To do several things on one condition, put them in braces: `if (x > 0) { a++; b++; }`.

The commonest mistake in C is to write `=` where you mean `==`. `if (mark = 72)` is not a comparison: it puts 72 in `mark`, and since 72 is not zero, it is always true.

When one number is to be compared with many fixed values, `switch` is neater:

```c
// expect: exit 2
// screen: 0 two
int main(void)
{
    int n = 2;
    cls();
    switch (n) {
    case 1:
        puts("one");
        break;
    case 2:
        puts("two");
        break;
    default:
        puts("many");
        break;
    }
    return n;
}
```

Each `case` runs on from where it starts until a `break`, so end every case with one. See the keywords [if](03_keywords.md#if), [else](03_keywords.md#else) and [switch](03_keywords.md#switch).

## Chapter 7 -- Doing things again

A **loop** repeats statements. `while` repeats as long as its condition is true:

```c
// expect: exit 55
// screen: 0 total 55
int main(void)
{
    int i = 1, total = 0;
    cls();
    while (i <= 10) {
        total += i;
        i++;
    }
    printf("total %d\n", total);
    return total;
}
```

If the condition is false at the start, the loop never runs. If it never becomes false, the loop never ends; press **BREAK** (CAPS SHIFT and SPACE) to stop a program. The loop with a counter is so common that `for` puts the three parts together: the start, the condition and the step.

```c
// expect: exit 6
// screen: 0 1 4 9 16 25
// screen: 1 1 2 3
// screen: 2 2 4 6
// screen: 3 3 6 9
int main(void)
{
    int i, r, c;
    cls();
    for (i = 1; i <= 5; i++)
        printf("%d ", i * i);
    printf("\n");
    for (r = 1; r <= 3; r++) {
        for (c = 1; c <= 3; c++)
            printf("%d ", r * c);
        printf("\n");
    }
    return i;
}
```

The program ends with `return i`, and the report says `EXIT 6`: after the first loop, `i` is 6, the first number for which `i <= 5` was false. The second loop is **nested** inside the first: for each row `r`, the inner loop counts across the columns `c`.

`break` leaves a loop at once, and `continue` skips the rest of this turn and goes on to the next:

```c
// expect: exit 56
// screen: 0 odd 25, seven 56
int main(void)
{
    int i, odd = 0;
    for (i = 1; i <= 9; i++) {
        if (i % 2 == 0)
            continue;
        odd += i;
    }
    for (i = 51; i < 100; i++)
        if (i % 7 == 0)
            break;
    cls();
    printf("odd %d, seven %d\n", odd, i);
    return i;
}
```

The first loop adds only the odd numbers (1, 3, 5, 7, 9); the second stops at the first multiple of 7 above 50. There is also `do ... while (condition);`, which tests at the end, so it always runs at least once.

A loop can go along a string until it finds the zero that ends it:

```c
// expect: exit 3
// screen: 0 e count 3
char *word = "excellent";
int main(void)
{
    int i = 0, n = 0;
    while (word[i] != 0) {
        if (word[i] == 'e')
            n++;
        i++;
    }
    cls();
    printf("e count %d\n", n);
    return n;
}
```

See the keywords [while](03_keywords.md#while), [for](03_keywords.md#for), [do](03_keywords.md#do), [break](03_keywords.md#break) and [continue](03_keywords.md#continue).

## Chapter 8 -- Functions

You have been writing a function all along: `main`. You can write others, to give a name to a piece of work and to use it many times. A function says what it needs (its **parameters**) and what type of value it gives back:

```c
// expect: exit 25
// screen: 0 5 squared is 25
int square(int n)
{
    return n * n;
}
int main(void)
{
    cls();
    printf("%d squared is %d\n", 5, square(5));
    return square(5);
}
```

`square` needs one `int`, which it calls `n` inside, and gives back an `int`. `square(5)` **calls** it, and the call is replaced by the value. A function that gives nothing back is `void`:

```c
// expect: exit 120
// screen: 0 -----
// screen: 1 5! = 120
void dashes(int n)
{
    while (n--)
        putchar('-');
    puts("");
}
int fact(int n)
{
    if (n <= 1)
        return 1;
    return n * fact(n - 1);
}
int main(void)
{
    cls();
    dashes(5);
    printf("5! = %d\n", fact(5));
    return fact(5);
}
```

A function may call itself; that is **recursion**. `fact(5)` is 5 times `fact(4)`, and so on down to `fact(1)`, which is 1. A function can be called before its definition in the file. A function may have up to 16 parameters.

Variables declared inside a function are **local**: they exist only while it runs, and each call has its own. A variable declared outside every function is **global** and is shared.

```c
// expect: exit 3
// screen: 0 hits 3
int count = 0;
void hit(void)
{
    count++;
}
int main(void)
{
    hit();
    hit();
    hit();
    cls();
    printf("hits %d\n", count);
    return count;
}
```

Parameters are **copies**: a function that changes its own `n` does not change the caller's variable. Chapter 10 shows how to let a function change the caller's variable. A function can be as long as you like, but locals of one function take at most 255 bytes. See [return](03_keywords.md#return) and the concept [Memory](05_concepts.md#memory).

## Chapter 9 -- Lists of things

An **array** is a numbered row of variables of one type. `int a[5]` holds five `int`s, numbered **0 to 4**. A global array can be given its values at the start:

```c
// expect: exit 15
// screen: 0 1 2 3 4 5
// screen: 1 sum 15
int a[5] = { 1, 2, 3, 4, 5 };
int main(void)
{
    int i, sum = 0;
    cls();
    for (i = 0; i < 5; i++) {
        printf("%d ", a[i]);
        sum += a[i];
    }
    printf("\nsum %d\n", sum);
    return sum;
}
```

A local array cannot have a list of values in Leap-C. Fill it with a loop, or make it `static` (or global) to give it a list. `sizeof` gives the size of an array in bytes:

```c
// expect: exit 25
// screen: 0 4 25 12
int main(void)
{
    int sq[6];
    int i;
    for (i = 0; i < 6; i++)
        sq[i] = i * i;
    cls();
    printf("%d %d %d\n", sq[2], sq[5], sizeof sq);
    return sq[5];
}
```

Six `int`s of two bytes make 12. Arrays can have more than one dimension, a table:

```c
// expect: exit 7
// screen: 0 6 7
int grid[2][3] = { { 1, 2, 3 }, { 4, 5, 6 } };
int main(void)
{
    cls();
    printf("%d %d\n", grid[1][2], grid[0][2] + grid[1][0]);
    return grid[0][2] + grid[1][0];
}
```

**Take care.** Leap-C does not check that an index is inside the array. `a[5]` above would read whatever is in memory beyond the array, and `a[5] = 0;` would damage it. This is C. The concept [Arrays](05_concepts.md#arrays) has the rest.

## Chapter 10 -- Pointers, gently

Every variable lives at an address in memory. `&x` is "the address of `x`". A **pointer** is a variable that holds an address. `int *p` declares `p` as a pointer to an `int`, and `*p` means "the thing `p` points to".

That lets a function change its caller's variables. Give the function their addresses:

```c
// expect: exit 7
// screen: 0 a=3 b=7
void swap(int *p, int *q)
{
    int t = *p;
    *p = *q;
    *q = t;
}
int main(void)
{
    int a = 7, b = 3;
    cls();
    swap(&a, &b);
    printf("a=%d b=%d\n", a, b);
    return b;
}
```

The name of an array, used alone, is the address of its first element. Adding 1 to a pointer moves it to the next element, whatever its size:

```c
// expect: exit 20
// screen: 0 10 20 30
// screen: 1 20
int a[3] = { 10, 20, 30 };
int main(void)
{
    int *p = a;
    cls();
    printf("%d %d %d\n", *p, *(p + 1), p[2]);
    p++;
    printf("%d\n", *p);
    return *p;
}
```

`*(p + 1)` and `p[1]` mean the same. A string in double quotes is also a pointer to its first character, which is why a function such as `puts` accepts one. A pointer to nothing is the number 0, called NULL: `malloc` returns it when no memory is left, and it is not checked for you if you use it. See the concept [Pointers](05_concepts.md#pointers), [malloc](04_library.md#malloc) and [free](04_library.md#free).

## Chapter 11 -- Structures

Sometimes values belong together. A **struct** groups variables of different types under one name. Its parts are **members**, reached with a dot:

```c
// expect: exit 12
// screen: 0 at 12,6
struct point { int x; int y; };
struct point p;
int main(void)
{
    struct point *q = &p;
    p.x = 12;
    p.y = 5;
    q->y = q->y + 1;
    cls();
    printf("at %d,%d\n", p.x, p.y);
    return p.x;
}
```

Through a pointer to a struct, the member is reached with `->` (a minus and a greater-than, typed with SYMBOL SHIFT and J, then SYMBOL SHIFT and T): `q->y` means `(*q).y`. A `typedef` gives a type a shorter name, and structures can be put in arrays:

```c
// expect: exit 57
// screen: 0 middle x 3, sum 57
typedef struct point { int x; int y; } Point;
Point pts[3] = { { 1, 2 }, { 3, 4 }, { 5, 6 } };
int main(void)
{
    int i, sum = 0;
    Point *q = &pts[1];
    q->y = 40;
    for (i = 0; i < 3; i++)
        sum += pts[i].x + pts[i].y;
    cls();
    printf("middle x %d, sum %d\n", pts[1].x, sum);
    return sum;
}
```

A struct takes up exactly the sum of its members' sizes, with no padding: `Point` is 4 bytes. Leap-C cannot pass a struct to a function, return one or assign one with `=`; use pointers (and `memcpy` to copy). An `enum` names a set of whole numbers, counting from 0:

```c
// expect: exit 2
// screen: 0 day 2
enum day { MON, TUE, WED };
int main(void)
{
    enum day d = WED;
    cls();
    printf("day %d\n", d);
    return d;
}
```

See the keywords [struct](03_keywords.md#struct), [enum](03_keywords.md#enum) and [typedef](03_keywords.md#typedef).

## Chapter 12 -- The screen and colour

The text screen has 24 rows (0 to 23) and 32 columns (0 to 31). `at(row, col)` moves where the next text goes; `tab(col)` moves along the row. The colours are numbers 0 to 7: black, blue, red, magenta, green, cyan, yellow, white. `ink` sets the colour of the letters, `paper` the colour behind them and `border` the colour of the border.

```c
// expect: exit 0
// screen: 3         RED ON YELLOW
// screen: 5 Back to normal
// screen: 7 tab:        here
// attr: 3 8 0x32
int main(void)
{
    cls();
    border(1);
    at(3, 8);
    ink(2);
    paper(6);
    print("RED ON YELLOW");
    at(5, 0);
    ink(0);
    paper(7);
    print("Back to normal");
    at(7, 0);
    print("tab:");
    tab(12);
    print("here");
    return 0;
}
```

`print` is like `puts` but without the new line. The colours stay as set until you set them again, and `cls()` clears the screen to the current ones. `bright(1)` makes colours brighter, `flash(1)` makes them flash, `inverse(1)` swaps ink and paper, and `over(1)` prints by exclusive-or, which lets a second print erase the first; use 0 to turn each off.

The `attr: 3 8 0x32` line checks the cell's **attribute byte**: yellow paper (6, times 8 is 48, or `0x30`) and red ink (2) make `0x32`. `attr(row, col)` reads one in a program.

Be careful of the bottom row. Printing past the last row of the screen scrolls it. See [at](04_library.md#at), [ink](04_library.md#ink), [paper](04_library.md#paper), [border](04_library.md#border) and [cls](04_library.md#cls).

## Chapter 13 -- Graphics

The screen is 256 pixels across (x from 0 to 255) and 192 down (y from 0 to 191). **The point (0, 0) is the top left corner**, and y grows downwards. `plot(x, y)` sets a pixel; `draw(x0, y0, x1, y1)` draws a line between two points, both ends included; `point(x, y)` tells you whether a pixel is set (1) or not (0).

```c
// expect: exit 1
// pixel: 20 20 1
// pixel: 120 80 1
// pixel: 70 50 1
// pixel: 71 50 0
// attr: 2 2 0x39
int main(void)
{
    cls();
    ink(1);
    draw(20, 20, 120, 20);
    draw(120, 20, 120, 80);
    draw(120, 80, 20, 80);
    draw(20, 80, 20, 20);
    plot(70, 50);
    return point(70, 50) + point(71, 50);
}
```

That draws a blue rectangle with a dot in the middle. The dot is set and its neighbour is not, so the program returns 1 + 0. Pixels take their colour from the character cell they are in (8 by 8 pixels): `ink` decides the colour of what you draw, and the whole cell takes it.

A loop makes patterns:

```c
// expect: exit 0
// pixel: 0 191 1
// pixel: 128 100 1
// pixel: 248 191 1
int main(void)
{
    int x;
    cls();
    for (x = 0; x < 256; x += 8)
        draw(x, 191, 128, 100);
    return 0;
}
```

Thirty-two lines fan out from the point (128, 100). For circles and rectangles, load the **shapes** library from tape: type `LIB "shapes"` on the last line, and play `shapes.tzx` (Chapter 17 says how tapes work). The report is `LIBRARY shapes: 3 FUNCTIONS`. Then `circle`, `box` and `isqrt` can be called like any other function.

```c
// library: shapes
// expect: exit 0
// pixel: 158 96 1
int main(void)
{
    cls();
    circle(128, 96, 30);
    box(60, 40, 196, 152);
    return 0;
}
```

Without the library the same program is `ERROR 70: UNDEFINED FUNCTION`. [Part 6](06_libraries.md) describes libraries and how to write one. The TS2068's high-resolution colour mode, `mode(1)`, is the concept [High resolution](05_concepts.md#high-resolution). See [plot](04_library.md#plot), [draw](04_library.md#draw) and [point](04_library.md#point).

## Chapter 14 -- Sound

The TS2068 has an AY sound chip. `beep(frames, semitone)` plays a note for a number of **frames** (a 60th of a second on a TS2068; a 50th on ZEsarUX). Semitone 0 is middle C, 1 is the next note up, and so on, from -60 to 69. A scale goes up by steps of 2, 2, 1, 2, 2, 2, 1:

```c
// expect: exit 0
int scale[8] = { 0, 2, 4, 5, 7, 9, 11, 12 };
int main(void)
{
    int i;
    for (i = 0; i < 8; i++)
        beep(10, scale[i]);
    pause(30);
    for (i = 7; i >= 0; i--)
        beep(10, scale[i]);
    return 0;
}
```

`pause(n)` waits n frames. A semitone out of range stops the program with runtime error 4 (`BAD ARGUMENT`; Chapter 18). `sound(reg, value)` writes directly into one of the 16 registers of the AY chip, for sounds of your own design. See [beep](04_library.md#beep), [sound](04_library.md#sound) and [pause](04_library.md#pause).

## Chapter 15 -- The keyboard

A program can read keys. `getkey()` **waits** for a key and returns its code. This program counts keys until you press `q`:

```c
// keys: "abq"
// expect: exit 3
// screen: 0 3 keys
int main(void)
{
    int n = 0, k;
    cls();
    do {
        k = getkey();
        n++;
    } while (k != 'q');
    printf("%d keys\n", n);
    return n;
}
```

The `keys:` line is how the test "presses" a, b and q. At the machine you press them yourself. `inkey()` only **looks**: it returns the key pressed since the last call, or 0 when none was, and the program carries on. Games use it so that things keep moving. In this program, to keep the test simple, `getkey()` makes the star wait for you:

```c
// keys: "ddaq"
// expect: exit 11
// screen: 5            *
int main(void)
{
    int x = 10, k;
    do {
        cls();
        at(5, x);
        print("*");
        k = getkey();
        if (k == 'a')
            x--;
        if (k == 'd')
            x++;
    } while (k != 'q');
    return x;
}
```

Press `a` to move the star left, `d` to move it right, `q` to stop. (To run something at the same time, use `inkey()` instead of `getkey()` in the loop, and `pause(1)` to slow the loop down.)

To read a whole line, use `gets(buf, max)`, which reads at most `max - 1` characters, lets the user correct with DELETE, and stops at ENTER. `atoi` turns the text into a number:

```c
// keys: "21" ENTER
// expect: exit 42
// screen: 0 Number? 21
// screen: 1 Double is 42
char buf[8];
int main(void)
{
    int n;
    cls();
    print("Number? ");
    gets(buf, sizeof buf);
    n = atoi(buf) * 2;
    printf("Double is %d\n", n);
    return n;
}
```

Special keys read as ASCII codes: 8 for DELETE and 13 for ENTER. **BREAK** is not read by the program: it stops it (see the concept [BREAK](05_concepts.md#break)). See [getkey](04_library.md#getkey), [inkey](04_library.md#inkey) and [gets](04_library.md#gets).

## Chapter 16 -- Numbers with fractions

A `float` holds a number with a fraction. `double` is the same type. It uses the TS2068's own 5-byte number format: about 9.6 digits, up to 1.7E38. It is **not** the IEEE format of other computers. Where whole numbers are mixed with `float`s, the whole numbers are converted for you, and a `float` stored in an `int` loses its fraction. `%f` prints 6 decimals, and `%.2f` two.

```c
// expect: exit 314
// screen: 0 3 3.5
// screen: 1 area 314.16
float area(float r)
{
    return 3.14159265 * r * r;
}
int main(void)
{
    cls();
    printf("%d %.1f\n", 7 / 2, 7 / 2.0);
    printf("area %.2f\n", area(10));
    return (int)area(10);
}
```

`7 / 2` has two whole numbers, so it is a whole number, 3. `7 / 2.0` has a fraction in it, so the answer, 3.5, has one too. `(int)` is a **cast**: it makes `area(10)` a whole number, dropping the fraction, so the exit value is 314.

A table of Celsius and Fahrenheit:

```c
// expect: exit 0
// screen: 0 -40 -40.0
// screen: 1 37 98.6
// screen: 2 100 212.0
int temps[3] = { -40, 37, 100 };
int main(void)
{
    int i;
    cls();
    for (i = 0; i < 3; i++)
        printf("%d %.1f\n", temps[i], temps[i] * 1.8 + 32);
    return 0;
}
```

Some things to know. Fractions such as 0.1 are not exact in binary, so do not test floats for equality with `==`; compare against a small tolerance. Float arithmetic is far slower than integer arithmetic: a multiplication takes about 6 milliseconds. Use integers where you can. There is no `sqrt`, `sin` or other maths library; they are short to write in C. This one finds a square root by repeated averaging:

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

A float that overflows, or a float divided by zero, stops the program with runtime error 6 (`NUMBER TOO BIG`). See the concept [Floating point](05_concepts.md#floating-point).

## Chapter 17 -- Keeping your work

When you switch off, the program is lost. Save it on tape first. On the empty last line type:

```
SAVE "myprog"
```

The name has 1 to 10 characters. While the tape moves, the status row shows `SAVING myprog`, and when it is done the report is `SAVED myprog`. To get the program back, `NEW` and then `LOAD "myprog"`; the report is `LOADED myprog` and the program replaces the one in the editor. `LOAD ""` loads the next program on the tape, whatever its name. `VERIFY "myprog"` checks that the tape matches what is in the machine: `VERIFIED myprog`. If something goes wrong the report is `LOAD FAILED`, `VERIFY FAILED` or `BAD TAPE VERSION` (a tape that is not Leap-C's). Press **BREAK** to stop a tape command.

In an emulator a tape is a file (`.tzx` or `.tap`), and you work the "recorder" through the emulator's menu. **Fuse** can record a `SAVE` so that you can write it to a file; ZEsarUX 13.0 and TSRun cannot. The [emulator guide](../EMULATORS.md) (section 7) gives the steps for each. On a PC you can also write a program in a text editor and turn it into a tape with `tools/c2tape.py`.

A program can keep its own data on tape too. `tape_save(name, addr, len)` writes `len` bytes starting at `addr`; `tape_load(name, addr, max)` reads them back and returns how many it loaded, or a negative number if it failed (-1 nothing loaded; -2 the data failed part-way; -3 not a Leap-C tape).

```c
char scores[20];

tape_save("scores", scores, sizeof scores);
len = tape_load("scores", scores, sizeof scores);
```

Program tapes and data tapes are different kinds: `LOAD` skips data tapes, and `tape_load` skips programs. Leap-C waits about two minutes for a tape to start. See the keywords [SAVE](03_keywords.md#save), [LOAD](03_keywords.md#load) and [VERIFY](03_keywords.md#verify), and the concept [Tapes](05_concepts.md#tapes).

## Chapter 18 -- When things go wrong

Things go wrong in three ways.

**The compiler refuses the program.** You get `ERROR n: MESSAGE` and `LINE m` and nothing runs (Chapter 3). The commonest causes:

| You wrote | You get |
|---|---|
| a missing `;`, `)` or `}` | `20 SYNTAX ERROR` |
| a name that was never declared (or misspelt) | `23 UNDECLARED IDENTIFIER`, with the name |
| a call to a function that does not exist | `70 UNDEFINED FUNCTION` |
| a number where a pointer is wanted, or the like | `40 TYPE MISMATCH` or `51 BAD OPERAND TYPE` |
| something Leap-C does not have (`long`, `union`) | `1 NOT SUPPORTED` |
| no `main` | `71 NO MAIN FUNCTION` |

For a name that is wrong, the report shows it too, and the cursor stops just after it:

```c
// expect: error E_UNDECL 5
int main(void)
{
    int count = 0;
    return cont;
}
```

reports `ERROR 23: UNDECLARED IDENTIFIER` and `LINE 5  'cont'`. (Without the `//` line it is line 4.)

**The program stops with a runtime error.** The report is `RUNTIME ERROR n: MESSAGE` and `LINE m`, where m is the line on which the function that failed **starts**; a key returns you to the editor with the cursor there. The ones you are most likely to meet:

```c
// expect: rterror 4
int main(void)
{
    beep(1, 100);
    return 0;
}
```

is `RUNTIME ERROR 4: BAD ARGUMENT`, a library function given a value out of range (the semitone of a note goes only to 69). A function that calls itself without end ends with `1 STACK OVERFLOW`; a float divided by zero gives `6 NUMBER TOO BIG`:

```c
// expect: rterror 6
int main(void)
{
    float zero = 0;
    return 1 / zero;
}
```

**The program runs, but does the wrong thing.** C does not catch these for you. Dividing a whole number by zero gives 0, with no error at all. An index past the end of an array, or a pointer that points nowhere, quietly reads or writes the wrong place. `=` where `==` was meant is a valid program. When the output is wrong, print the variables with `printf` as the program goes along, and look at them.

```c
// expect: exit 0
int main(void)
{
    int z = 0;
    return 7 / z + 7 % z;
}
```

Press **BREAK** (CAPS SHIFT and SPACE) to stop a program that does not finish; the report is `BREAK` and the line. When a program is too big, `FREE` shows the space left, and `ERROR 100: OUT OF MEMORY` or `ERROR 101: PROGRAM TOO BIG` means shorten it. Every message and number is in the appendices ([A](08_appendices.md), [B](08_appendices.md), [C](08_appendices.md)) and the concept [Errors](05_concepts.md#errors).

## Where next

* Look up any word in [Part 3, Keywords](03_keywords.md), and any function in [Part 4, The library](04_library.md): every entry has examples you can type in.
* Read the [Concepts](05_concepts.md) when you wonder *why*: how memory is used, what is different from standard C, what each error means.
* Try the programs in [Part 7](07_examples.md) and change them.
* Add circles and rectangles with [Part 6](06_libraries.md), or write a library of your own.
* Use [EXAMPLES.md](../EXAMPLES.md) in the repository for more programs, and tell the project what was hard: [BETA_TESTING.md](../BETA_TESTING.md) says how to report.
