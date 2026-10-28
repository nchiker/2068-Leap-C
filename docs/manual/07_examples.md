# Part 7 -- Practical examples

Complete programs, each of which does something useful or amusing. Type one in, `RUN` it, then change it: that is the best way to learn.

**Every program in this part is a test**, except the last, which needs a tape. The lines at the top that begin `// expect:`, `// screen:`, `// pixel:`, `// keys:` and `// library:` are the checked results (see [Appendix I](08_appendices.md#appendix-i-how-this-manual-was-checked)): the build compiles each program on the ROM, runs it, and fails if the exit status, the text on the screen or the pixels are not what those lines say. The output shown after each program is what its `// screen:` lines require. The lines are comments to the compiler, so you can type the programs with them or without them (typed without them, the line numbers in a compile error are smaller by the number of comment lines).

For the programs that read the keyboard, the keys that were typed are the `// keys:` line. The programs print from the top of the screen, so each begins with `cls()`; the report that `RUN` leaves in rows 22 and 23 (`EXIT n`) is not shown.

---

## 1. A multiplication table

Two nested loops, and a width in `%4d` to line the columns up. The `printf("\n")` ends each row.

```c
// expect: exit 0
// screen: 0    1   2   3   4   5
// screen: 1    2   4   6   8  10
// screen: 2    3   6   9  12  15
// screen: 3    4   8  12  16  20
// screen: 4    5  10  15  20  25
int main(void)
{
    int row, col;
    cls();
    for (row = 1; row <= 5; row++) {
        for (col = 1; col <= 5; col++)
            printf("%4d", row * col);
        printf("\n");
    }
    return 0;
}
```

```text
   1   2   3   4   5
   2   4   6   8  10
   3   6   9  12  15
   4   8  12  16  20
   5  10  15  20  25
```

(`%4d` prints a number right-aligned in four columns; a number that is longer is printed whole.)

Ideas: make the table 9 by 9 (with `%4d` a row of nine numbers is 36 columns, wider than the screen: use `%3d`); print the row and column numbers as a heading.

## 2. Prime numbers

The sieve of Eratosthenes with an array: cross out the multiples of each number, and what is left is prime. A global array starts as zeros.

```c
// expect: exit 10
// screen: 0 2 3 5 7 11 13 17 19 23 29
char crossed[30];
int main(void)
{
    int n, m, count = 0;
    cls();
    for (n = 2; n < 30; n++) {
        if (!crossed[n]) {
            printf("%d ", n);
            count++;
            for (m = n * 2; m < 30; m += n)
                crossed[m] = 1;
        }
    }
    return count;
}
```

```text
2 3 5 7 11 13 17 19 23 29
```

`main` returns the number of primes found, so the report at the bottom is `EXIT 10`.

Ideas: a bigger array (the numbers must still fit on the screen: a row holds 32 characters, and the text continues on the next row); count only the primes whose last digit is 3.

## 3. Fibonacci numbers

Each number is the sum of the two before it. A loop does it with three variables:

```c
// expect: exit 55
// screen: 0 0 1 1 2 3 5 8 13 21 34 55 89
// screen: 1 fib(10) = 55
int fib(int n)
{
    return n < 2 ? n : fib(n - 1) + fib(n - 2);
}
int main(void)
{
    int a = 0, b = 1, t, i;
    cls();
    for (i = 0; i < 12; i++) {
        printf("%d ", a);
        t = a + b;
        a = b;
        b = t;
    }
    printf("\nfib(10) = %d\n", fib(10));
    return fib(10);
}
```

```text
0 1 1 2 3 5 8 13 21 34 55 89
fib(10) = 55
```

The function `fib` is the same sequence by **recursion**, a function that calls itself. It is elegant, but much slower for big numbers, because it works every number out from scratch. Each call of a function takes stack: Leap-C stops a runaway recursion with a runtime error (see [Errors](05_concepts.md#errors)): a function with one `int` parameter and one `int` local can call itself about 190 levels deep.

Ideas: print the first 20 numbers (what happens after `fib(23)`? an `int` has 16 bits); use `unsigned`.

## 4. Sorting

A bubble sort. Passes through the array swap neighbours that are out of order until a pass makes no swap. The function takes a pointer to the array and its length and returns the number of swaps.

```c
// expect: exit 12
// screen: 0 5 7 12 23 32 34 48 62
// screen: 1 12 swaps
int d[8] = { 34, 7, 23, 32, 5, 62, 12, 48 };
int sort(int *a, int n)
{
    int i, t, swaps = 0, swapped = 1;
    while (swapped) {
        swapped = 0;
        for (i = 0; i < n - 1; i++) {
            if (a[i] > a[i + 1]) {
                t = a[i];
                a[i] = a[i + 1];
                a[i + 1] = t;
                swapped = 1;
                swaps++;
            }
        }
    }
    return swaps;
}
int main(void)
{
    int i, swaps;
    cls();
    swaps = sort(d, 8);
    for (i = 0; i < 8; i++)
        printf("%d ", d[i]);
    printf("\n%d swaps\n", swaps);
    return swaps;
}
```

```text
5 7 12 23 32 34 48 62
12 swaps
```

(Twelve is the number of pairs that were out of order to begin with: each swap puts exactly one pair right.)

To sort words, compare them with `strcmp` instead of `>`: `if (strcmp(a[i], a[i + 1]) > 0)` with an array of pointers to strings. Ideas: sort into descending order; sort 100 numbers from `rand()` and time it with `frames()`.

## 5. A secret code

A Caesar cipher: each capital letter is moved along the alphabet by three places. A `char` holds a letter's code, so arithmetic on it is arithmetic on the alphabet; the remainder `%` makes the alphabet wrap.

```c
// expect: exit 11
// screen: 0 HELLO WORLD
// screen: 1 KHOOR ZRUOG
char msg[] = "HELLO WORLD";
char out[16];
int main(void)
{
    int i, k;
    cls();
    for (i = 0; msg[i]; i++) {
        k = msg[i];
        if (k >= 'A' && k <= 'Z')
            k = (k - 'A' + 3) % 26 + 'A';
        out[i] = k;
    }
    out[i] = 0;
    puts(msg);
    puts(out);
    return i;
}
```

```text
HELLO WORLD
KHOOR ZRUOG
```

`msg[]` takes its size from its string (12 bytes with the end mark). The loop stops at that mark, the character 0, which a `for` condition sees as false. The program returns the length, 11.

Ideas: decode (use `+ 23` instead of `+ 3`, or any number from 0 to 25); read the message with `gets` (example 6 shows how); let the shift be a variable.

## 6. Guess the number

The computer thinks of a number and you guess. `gets` reads a line (with DELETE working), `atoi` turns it into a number. The number here is fixed at 37 so that the page shows the same game every time; for a different game each time, use `rand()` and seed it with `srand(frames())` after a first key press (see [rand](04_library.md#rand) and [srand](04_library.md#srand)). The guesses typed here are 50, 25 and 37.

```c
// keys: "50" ENTER "25" ENTER "37" ENTER
// expect: exit 3
// screen: 0 Guess? 50
// screen: 1 Too high
// screen: 2 Guess? 25
// screen: 3 Too low
// screen: 4 Guess? 37
// screen: 5 Got it in 3 tries
char buf[8];
int main(void)
{
    int secret = 37, tries = 0, g;
    cls();
    do {
        print("Guess? ");
        gets(buf, sizeof buf);
        g = atoi(buf);
        tries++;
        if (g < secret)
            puts("Too low");
        else if (g > secret)
            puts("Too high");
    } while (g != secret);
    printf("Got it in %d tries\n", tries);
    return tries;
}
```

```text
Guess? 50
Too high
Guess? 25
Too low
Guess? 37
Got it in 3 tries
```

The buffer holds 7 characters and the end mark: `gets(buf, 8)` reads at most 7. `main` returns the number of tries.

Ideas: tell the player how many tries are left and end after seven; keep playing until the player types 0.

## 7. A menu

`getkey()` waits for a key and returns its code, and `switch` chooses what to do with it. A key that is not on the menu gets a question mark. The keys typed here are `1`, `2`, `x`, `2` and `3`.

```c
// keys: "12x23"
// expect: exit 12
// screen: 0 1 ADD 2   2 ADD 5   3 QUIT
// screen: 1 ?
// screen: 2 total 12
int main(void)
{
    int total = 0, k;
    cls();
    puts("1 ADD 2   2 ADD 5   3 QUIT");
    while ((k = getkey()) != '3') {
        switch (k) {
        case '1':
            total += 2;
            break;
        case '2':
            total += 5;
            break;
        default:
            puts("?");
        }
    }
    printf("total %d\n", total);
    return total;
}
```

```text
1 ADD 2   2 ADD 5   3 QUIT
?
total 12
```

Ideas: show the running total after every key; add a key that resets it; accept the letters `a`, `b` and `q` as well (give two `case` labels to the same code).

## 8. A temperature table

Numbers with fractions are `float`. `printf` prints them with `%f` (six decimals) or `%.1f` (one decimal, here). An integer in an expression with a `float` is converted first.

```c
// expect: exit 0
// screen: 0 C     F
// screen: 1 36    96.8
// screen: 2 37    98.6
// screen: 3 38    100.4
// screen: 4 39    102.2
// screen: 5 40    104.0
int main(void)
{
    int c;
    cls();
    puts("C     F");
    for (c = 36; c <= 40; c++)
        printf("%d    %.1f\n", c, c * 1.8 + 32);
    return 0;
}
```

```text
C     F
36    96.8
37    98.6
38    100.4
39    102.2
40    104.0
```

Decimal fractions such as 1.8 are not exact in binary, so the values are really a hair above or below: a `%.1f` shows them rounded. For the same reason, test floats with a tolerance and not with `==` (see [Floating point](05_concepts.md#floating-point)). A float calculation is much slower than an integer one (a multiplication takes about 6 ms), which does not matter in a table of five rows.

Ideas: print Celsius for Fahrenheit 0 to 100 in steps of 10; add a column of Kelvin.

## 9. Square roots

There is no maths library in Leap-C (no `sqrt`, no `sin`); the usual functions are short to write. This one uses Newton's method: a guess is improved by averaging it with *x* divided by itself, twenty times.

```c
// expect: exit 0
// screen: 0 sqrt(2) = 1.41421356
// screen: 1 sqrt(16) = 4.00
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
    printf("sqrt(16) = %.2f\n", root(16));
    return 0;
}
```

```text
sqrt(2) = 1.41421356
sqrt(16) = 4.00
```

A `float` is the TS2068 ROM's own 5-byte number: about 9.6 significant digits. `root(0)` divides by zero and stops the program with runtime error 6 (`NUMBER TOO BIG`): give the function a line that returns 0 for an *x* of 0 or less. For a whole number's root, when an integer will do, the shapes library has [isqrt](06_libraries.md#isqrt) (example 16).

## 10. A parabola

`plot(x, y)` sets a pixel; *x* is 0 to 255 from the left and *y* 0 to 191 **from the top**, so the curve is made upside down by subtracting from 191. The loop variable is `unsigned`: `x * x` is at most 36,481, which an `int` (up to 32,767) could not hold.

```c
// expect: exit 0
// screen: 0 PARABOLA
// pixel: 0 191 1
// pixel: 100 141 1
// pixel: 190 11 1
// pixel: 100 140 0
int main(void)
{
    unsigned x;
    cls();
    print("PARABOLA");
    for (x = 0; x < 192; x++)
        plot(x, 191 - x * x / 200);
    return 0;
}
```

The curve starts at the bottom left (0, 191) and climbs to (190, 11) near the top right. Run it and look; a `// pixel:` line gives the test one pixel to check, the picture is yours.

Ideas: use `draw` from each point to the next so that the curve has no gaps where it is steep; colour it with `ink(2)` before the loop; draw the axes with `draw(0, 191, 255, 191)` and `draw(0, 0, 0, 191)`.

## 11. Colour lines in high resolution

The TS2068's high-resolution colour mode uses the second display file, the memory at `$6000-$77FF`. A program that uses `mode(1)` should say `#pragma hires` at its top: that keeps the compiled program out of that memory. Without the pragma, a large program could occupy the memory and `mode(1)` would stop with runtime error 3 (see [High resolution](05_concepts.md#high-resolution)). The program draws seven lines, each in a different ink, on a black screen, then returns to the normal mode.

```c
// expect: exit 0
// pixel: 40 41 1
// pixel: 215 47 1
// pixel: 39 41 0
#pragma hires
int main(void)
{
    int i;
    paper(0);
    cls();
    mode(1);
    for (i = 1; i < 8; i++) {
        ink(i);
        draw(40, 40 + i, 215, 40 + i);
    }
    mode(0);
    ink(0);
    paper(7);
    return 0;
}
```

Seven lines of 176 pixels are drawn, at 41 to 47 pixels from the top. The end of any program restores mode 0; calling `mode(0)` yourself, as here, puts the normal display back before the program ends.

Ideas: wait for a key with `getkey()` between `draw` and `mode(0)` to look at the picture; use `plot` to draw a diagonal and see what colours it gets.

## 12. Countdown

A countdown with a beep for each number. `beep(frames, semitone)` plays a note of that many frames (a frame is a 60th of a second on a TS2068, a 50th on ZEsarUX), semitone 0 being middle C; `pause(n)` waits *n* frames. Both stop at once if you press BREAK.

```c
// expect: exit 0
// screen: 0 3 2 1 GO
int main(void)
{
    int i;
    cls();
    for (i = 3; i > 0; i--) {
        printf("%d ", i);
        beep(5, i * 4);
        pause(10);
    }
    print("GO");
    return 0;
}
```

```text
3 2 1 GO
```

The pitch falls as the numbers do: the notes are the semitones 12, 8 and 4 above middle C. Ideas: a longer, higher note for GO; print one row for each number with `at(row, col)`; use `sound(reg, value)` to program the sound chip yourself (see [sound](04_library.md#sound)).

## 13. A character of your own

Codes 144 to 164 are 21 **user-defined characters**, eight bytes each, in memory from `$F180`. They are blank until a program writes them: the eight bytes are the eight rows of the picture, a 1 bit being ink. This program copies a face into the first one and prints it. (The face is symmetric left to right, so that it does not matter which end of a byte is the left of the picture.)

```c
// expect: exit 0
// pixel: 2 0 1
// pixel: 5 0 1
// pixel: 0 0 0
// pixel: 7 0 0
// pixel: 0 3 1
// pixel: 7 3 1
// pixel: 3 3 0
char face[8] = { 0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C };
int main(void)
{
    cls();
    memcpy((char *)0xF180, face, 8);
    putchar(144);
    return 0;
}
```

The face appears in the top left corner. Its eight rows, from the bytes (`#` is a 1 bit):

```text
..####..     0x3C
.#....#.     0x42
#.#..#.#     0xA5
#......#     0x81
#.#..#.#     0xA5
#..##..#     0x99
.#....#.     0x42
..####..     0x3C
```

The test checks that pixels 2 and 5 of row 0 are set and 0 and 7 are not, and that pixels 0 and 7 of row 3 are set and pixel 3 is not.

Ideas: fill an array of faces with `memcpy` and `UDG` codes 144, 145, ...; build an animation by changing the bytes between `pause` calls.

## 14. A list on the heap

`malloc` gives memory from the **heap** and `free` returns it. Here each number goes into a small `struct` that is linked to the one before. `malloc` returns NULL when nothing fits, which the program checks.

```c
// expect: exit 55
// screen: 0 25 16 9 4 1 = 55
struct node {
    int v;
    struct node *next;
};
int main(void)
{
    struct node *head = 0, *n;
    int i, sum = 0;
    cls();
    for (i = 1; i <= 5; i++) {
        n = malloc(sizeof(struct node));
        if (!n)
            return 1;
        n->v = i * i;
        n->next = head;
        head = n;
    }
    for (n = head; n; n = n->next) {
        printf("%d ", n->v);
        sum += n->v;
    }
    printf("= %d\n", sum);
    while (head) {
        n = head->next;
        free(head);
        head = n;
    }
    return sum;
}
```

```text
25 16 9 4 1 = 55
```

Each new node goes in front of the list, so the squares come out in the reverse of the order in which they were made. The last loop gives every block back; a program that ends without doing so leaves nothing behind either, because every run starts with a new, empty heap. How much heap there is, is the `HEAP h B` of the report (see [Memory](05_concepts.md#memory)).

Ideas: add a function that puts a node at the *end* of the list; delete the node holding 9; build the list from keys typed with `getkey()`.

## 15. A bullseye

*With the shapes library loaded (`LIB "shapes"`):* three concentric circles, and then one of them is rubbed out. `over(1)` makes `circle` draw by exclusive-or; since the library draws each point exactly once, a second `circle` call with the same arguments clears what the first drew (see [circle](06_libraries.md#circle)). The program tests that with `point` before and after.

```c
// library: shapes
// expect: exit 10
// screen: 0 BULLSEYE
// pixel: 128 76 1
// pixel: 128 56 0
// pixel: 128 36 1
// pixel: 68 96 1
// pixel: 88 96 0
// pixel: 128 96 0
int main(void)
{
    int r, before, after;
    cls();
    print("BULLSEYE");
    for (r = 20; r <= 60; r += 20)
        circle(128, 96, r);
    before = point(128, 56);
    over(1);
    circle(128, 96, 40);
    after = point(128, 56);
    over(0);
    return before * 10 + after;
}
```

`before` is 1 and `after` is 0, so the exit status is 10. Of the three circles (radii 20, 40 and 60), the middle one has gone and the outer two are left. Ideas: use `ink` to colour each ring (the cell takes the colour in which a point is drawn); make the rings move by drawing one, `pause`-ing, and drawing it again at the same place to rub it out.

## 16. A table of square roots

*With the shapes library loaded:* `isqrt(n)` is the largest whole number *r* with *r* x *r* not more than *n*. The array is `unsigned` so that 65535 fits; the largest root, of 65535, is 255.

```c
// library: shapes
// expect: exit 255
// screen: 0     N ROOT
// screen: 1     0    0
// screen: 2     2    1
// screen: 3    16    4
// screen: 4    99    9
// screen: 5 10000  100
// screen: 6 65535  255
unsigned t[6] = { 0, 2, 16, 99, 10000, 65535u };
int main(void)
{
    int i;
    cls();
    puts("    N ROOT");
    for (i = 0; i < 6; i++)
        printf("%5u %4u\n", t[i], isqrt(t[i]));
    return isqrt(t[5]);
}
```

```text
    N ROOT
    0    0
    2    1
   16    4
   99    9
10000  100
65535  255
```

The integer root of 99 is 9 (10 x 10 is 100). Compare with the floating-point `root` of example 9: this one is exact for whole numbers and much faster. Ideas: print, for each of the numbers, the square of its root and the difference from the number; use `isqrt` as the limit of the loop that tests whether a number is prime (a divisor larger than the root has a partner smaller than it).

## 17. A picture frame

*With the shapes library loaded:* a box round the screen and three circles in it, with a line of text and the exit status computed with `isqrt`. This is the hardware kit's check program H11 (with some pixel checks added): on a real machine it checks that a library can be loaded from a cassette.

```c
// library: shapes
// expect: exit 100
// screen: 0 SHAPES 1 12 255
// pixel: 8 8 1
// pixel: 247 183 1
// pixel: 128 8 1
// pixel: 8 100 1
// pixel: 247 100 1
// pixel: 128 86 1
// pixel: 128 56 1
// pixel: 128 26 1
// pixel: 128 9 0
int main(void)
{
    int r;
    cls();
    box(8, 8, 247, 183);
    for (r = 10; r <= 70; r += 30)
        circle(128, 96, r);
    printf("SHAPES %u %u %u", isqrt(2), isqrt(144), isqrt(65535u));
    return isqrt(10000);
}
```

```text
SHAPES 1 12 255
```

The three roots printed are those of 2, 144 and 65535, and the exit status, `EXIT 100`, is the root of 10000. Try removing the library (`LIB` on its own on the empty last line) and running again: `ERROR 70: UNDEFINED FUNCTION` names the first library function the program uses (see [Part 6](06_libraries.md#errors)).

## 18. A score on tape

A program can put its own data on cassette with `tape_save(name, addr, len)` and bring it back with `tape_load(name, addr, max)` (see [tape_save](04_library.md#tape_save), [tape_load](04_library.md#tape_load) and [Tapes](05_concepts.md#tapes)). This program keeps a score between sessions. It is **not an automated test**, since it needs a tape to be played and recorded; it follows the rules of those two functions exactly.

```c
/* A score kept on tape: L loads it, S saves it. */
int score;
int main(void)
{
    int k, n;
    cls();
    puts("L = load the score");
    puts("S = add 10 and save it");
    k = getkey();
    if (k == 'L' || k == 'l') {
        n = tape_load("hiscore", &score, sizeof score);
        if (n == sizeof score)
            printf("Score: %d\n", score);
        else
            printf("No score (%d)\n", n);
    } else {
        score += 10;
        printf("Saving %d\n", score);
        tape_save("hiscore", &score, sizeof score);
        puts("Saved");
    }
    return 0;
}
```

Run it, press `S`, and record the tape while it says `Saving 10` (in Fuse, start **Media, Tape, Record Start** first; ZEsarUX cannot record Leap-C's tapes; `docs/EMULATORS.md` section 7.3 has the steps). Run it again, press `L` and play the tape: it prints `Score: 10`. If no tape arrives, `tape_load` gives up after about two minutes and returns -1, and the program prints `No score (-1)`; a tape that is not Leap-C's returns -3 and one that failed in the middle of its data -2. While a block moves, `frames()` does not count and the screen shows stripes in the border. SPACE or BREAK stops either function with the BREAK report.

Ideas: keep a table of ten names and scores (a `struct` array, saved whole by passing its address and `sizeof` it); check a checksum of your own after loading.
