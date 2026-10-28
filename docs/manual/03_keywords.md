# Part 3 -- Keywords

Every keyword, directive, operator and command of Leap-C 1.0.0-beta.2, in alphabetical order. The 32 reserved words of C89 each have an entry, including the three that Leap-C does not support. Operators are grouped by kind (`Arithmetic operators`, `Bitwise operators` and so on), with a table of their precedence under `Operator precedence`. The commands you type on the editor's last line (`FREE`, `LIB`, `LIST`, `LOAD`, `NEW`, `RUN`, `SAVE`, `VERIFY`) are entered in the same alphabetical order. The functions of the built-in library, such as `printf` and `plot`, are in [Part 4](04_library.md).

## How to read an entry

Each entry gives the **syntax**, the **kind** of word, a description, examples and, where they matter, notes, the errors it can cause, and related entries.

| Notation | Meaning |
|---|---|
| `keyword` | type it exactly like this. C is case-sensitive: `while` is a keyword, `WHILE` is a name. (The commands `RUN`, `LIST` and so on may be typed in upper or lower case.) |
| *italics* | something you supply: an expression, a name, a statement |
| `...` | may be repeated |
| `a \| b` | one of the alternatives |

Where a part is optional, the entry shows each form on its own line instead of marking it, because C already uses `[ ]`, `{ }` and `|` for other purposes.

*Kinds* are: **keyword** (a reserved word of C), **directive** (a line that begins with `#`, handled before the program is compiled), **operator**, and **command** (typed alone on the empty last line of the editor; not allowed in programs).

Most examples are complete programs. The `//` lines at the top are ordinary comments to the compiler, so you can type the program with or without them; they state what the program does, and the build runs every one of them on the ROM and checks it.

| Line | Meaning |
|---|---|
| `// expect: exit N` | `main` returns *N*: the `EXIT` report |
| `// expect: error E_NAME L` | the compile stops with that error at line *L* of the example, counting the `//` lines |
| `// expect: rterror N` | the program stops with run-time error *N* |
| `// screen: R TEXT` | text row *R* (0 is the top) reads *TEXT* after the program has run |

Three things matter everywhere:

* **A program is a set of functions.** Statements live inside functions, and the program starts at `main`. A statement ends with `;`. (See [Programs](05_concepts.md#programs).)
* **Keywords turn bold** when you leave the line, so you can see at once that you typed one correctly. A name that merely contains a keyword (`int1`, `_if`), a keyword in capitals (`INT`), and the text of a string or comment are not highlighted.
* **A word that is not supported is not skipped.** The reserved words `long`, `union` and `volatile` give `ERROR 1: NOT SUPPORTED`, and so does anything else outside the language; Leap-C never compiles it into something different.

Examples that print call `cls()` first, because a program starts with the screen as the editor left it.

---

## Arithmetic operators

`+` `-` `*` `/` `%` -- **operator**

Addition, subtraction, multiplication, division and remainder. `+` and `-` also work as signs in front of one operand (`-a`, `+a`). `*` in front of one operand is something else: see `Pointer and address operators`.

`/` truncates toward zero, and `%` takes the sign of its left operand, so `-17 / 5` is -3 and `-17 % 5` is -2. **Dividing an integer by zero is not an error**: the quotient is 0 and the remainder is 0. An `int` is 16 bits and **wraps around**: `32767 + 1` is -32768; an `unsigned` wraps from 0 down to 65535.

```c
// expect: exit 0
// screen: 0 3 2 -3 -2
// screen: 1 0 0
// screen: 2 -32768 65535
// screen: 3 1.50
int main(void)
{
    int a = 17, b = 5, z = 0, big = 32767;
    unsigned u = 0;
    cls();
    printf("%d %d %d %d\n", a / b, a % b, -a / b, -a % b);
    printf("%d %d\n", a / z, a % z);
    printf("%d %u\n", big + 1, u - 1);
    printf("%.2f\n", 3 / 2.0);
    return 0;
}
```

**Notes.**

* The usual conversions apply: a `char` becomes an `int`; if either operand is `unsigned`, both are `unsigned`; if either is floating, both are (see [Conversions](05_concepts.md#conversions)).
* `+ - * /` work on floating operands too. A floating `*` takes about 6 ms and a floating `/` longer; use integers where you can (see [Floating point](05_concepts.md#floating-point)).
* `%` takes integers only.
* A pointer plus or minus an integer is a pointer, moved by that many elements; one pointer minus another is an `int` (see `Pointer and address operators`). Adding two pointers is an error.
* Constant expressions are worked out when the program is compiled.

**Errors.**

| Mistake | What happens |
|---|---|
| `%` with a floating operand | `ERROR 51: BAD OPERAND TYPE` |
| a pointer times, divided by or `%` anything; the sign `-` of a pointer; two pointers added | `ERROR 51: BAD OPERAND TYPE` |
| a floating overflow, or a floating number divided by zero, at run time | run-time error 6, `NUMBER TOO BIG` |
| the same in a constant expression | `ERROR 16: NUMBER TOO LARGE` |

```c
// expect: error E_OPERAND 4
int main(void)
{
    return 5 % 2.0;
}
```

**See also** `Increment and decrement`, `Assignment operators`, `Operator precedence`, [Numbers](05_concepts.md#numbers), [Types](05_concepts.md#types).

---

## Assignment operators

*lvalue* `=` *expression*, *lvalue* `+=` *expression*, and likewise `-=` `*=` `/=` `%=` `&=` `|=` `^=` `<<=` `>>=` -- **operator**

`=` stores the value of the expression in the object on its left, converting it to that object's type, and gives the value stored. Each of the others is shorthand: `n += 4` means `n = n + 4`, except that `n` is worked out only once.

```c
// expect: exit 0
// screen: 0 3 5 8
int main(void)
{
    int n = 10, m = 3, a, b;
    n += 4;  n -= 2;  n *= 3;  n /= 5;  n %= 4;
    m <<= 3;  m |= 5;  m ^= 9;  m &= 22;  m >>= 2;
    a = b = 4;
    cls();
    printf("%d %d %d\n", n, m, a + b);
    return 0;
}
```

Here `n` goes 10, 14, 12, 36, 7, 3 and `m` goes 3, 24, 29, 20, 20, 5. The last statement shows that `=` groups from the right: `a = b = 4` stores 4 in `b`, then in `a`.

**Notes.**

* The left side must be an *lvalue*: a variable, an array element, `*p`, a structure member. An array as a whole is not one (`a = b` for two arrays is an error); copy the elements, or use `memcpy`.
* **A structure cannot be assigned** (`v = w`): copy the members, or use `memcpy` and pointers.
* A pointer takes only another pointer of the same type, a `void *`, or the constant `0`.
* A floating value assigned to an integer loses its fraction (it is cut toward zero). The compound forms `+= -= *= /=` work on floating objects; `%= &= |= ^= <<= >>=` do not.
* Assigning to a `const` object is an error.

**Errors.**

| Mistake | What happens |
|---|---|
| the left side is not an lvalue (`5 = 3`, an array, a call) | `ERROR 53: NOT AN LVALUE` |
| the left side is `const` | `ERROR 54: ASSIGNMENT TO CONST` |
| a pointer assigned from a pointer of another type without a cast, or from an integer other than 0 | `ERROR 40: TYPE MISMATCH` |
| one structure assigned to another | `ERROR 1: NOT SUPPORTED` |

```c
// expect: error E_LVALUE 4
int main(void)
{
    5 = 3;
    return 0;
}
```

**See also** `Bitwise operators`, `Arithmetic operators`, `Casts`, `const`, [Expressions](05_concepts.md#expressions), [Conversions](05_concepts.md#conversions).

---

## auto

`auto` *declaration* -- **keyword**

A storage-class word for a local variable: `auto int n;`. It is accepted and **ignored**, because a variable declared in a function is automatic anyway.

```c
// expect: exit 5
int main(void)
{
    auto int n = 5;
    return n;
}
```

**Notes.**

* Declared outside any function, `auto` is an error: there is no automatic storage there.
* Only one storage class may be given: `auto static` is an error.

**Errors.**

| Mistake | What happens |
|---|---|
| `auto` at file scope | `ERROR 26: BAD STORAGE CLASS` |
| two storage classes in one declaration | `ERROR 26: BAD STORAGE CLASS` |

```c
// expect: error E_STORAGE 2
auto int x;
int main(void) { return 0; }
```

**See also** `register`, `static`, `extern`, [Memory](05_concepts.md#memory).

---

## Bitwise operators

`&` `|` `^` `~` `<<` `>>` -- **operator**

`a & b`, `a | b` and `a ^ b` work bit by bit: and, or, exclusive-or. `~a` flips every bit. `a << n` shifts the bits of `a` left by *n* places, and `a >> n` right.

```c
// expect: exit 0
// screen: 0 8 14 6 -13
// screen: 1 48 3 -4 1
int main(void)
{
    int a = 12, b = 10, c = -16;
    unsigned u = 0x8000;
    cls();
    printf("%d %d %d %d\n", a & b, a | b, a ^ b, ~a);
    printf("%d %d %d %u\n", a << 2, a >> 2, c >> 2, u >> 15);
    return 0;
}
```

**Notes.**

* The operands are integers, 16 bits wide. `>>` of a **signed** value is an arithmetic shift (the sign is kept: `-16 >> 2` is -4); `>>` of an `unsigned` value fills with zeros.
* Do not confuse `&` and `|` with `&&` and `||`, which test truth (see `Logical operators`). A single `&` in front of one operand is the address operator.
* `&` binds more loosely than `==`: `x & 1 == 0` means `x & (1 == 0)`. Write the brackets (see `Operator precedence`).

**Errors.**

| Mistake | What happens |
|---|---|
| a floating operand | `ERROR 51: BAD OPERAND TYPE` |
| a pointer operand of `~`, `<<`, `>>` | `ERROR 51: BAD OPERAND TYPE` |

```c
// expect: error E_OPERAND 5
float f = 1.0;
int main(void)
{
    return f & 1;
}
```

**See also** `Logical operators`, `Assignment operators`, [Numbers](05_concepts.md#numbers).

---

## break

`break;` -- **keyword**

Leaves the nearest enclosing `for`, `while`, `do` or `switch` at once. The program goes on with the statement after it.

```c
// expect: exit 4
int main(void)
{
    int i;
    for (i = 0; i < 10; i++)
        if (i == 4)
            break;
    return i;
}
```

**Notes.**

* In a `switch`, `break` is how you stop one `case` from running on into the next.
* Only the innermost loop or `switch` is left. To get out of several, use `goto`.

**Errors.**

| Mistake | What happens |
|---|---|
| `break` outside a loop or `switch` | `ERROR 72: MISPLACED BREAK` |

```c
// expect: error E_BREAK 4
int main(void)
{
    break;
    return 0;
}
```

**See also** `continue`, `switch`, `goto`, `for`, `while`, `do`.

---

## case

`case` *constant* `:` -- **keyword**

A label inside a `switch`. When the value of the `switch` expression equals the constant, the program continues from the statement after the label. A constant may be a number, a character such as `'a'`, an `enum` name, or a constant expression. Labels do not stop the program: it runs on into the next one unless a `break` (or a `return`) intervenes.

```c
// expect: exit 0
// screen: 0 13 3 7 99
int f(int v)
{
    int r = 0;
    switch (v) {
    case 1:   r = 10;
    case 2:   r += 3; break;
    case 'a': r = 7; break;
    default:  r = 99;
    }
    return r;
}
int main(void)
{
    cls();
    printf("%d %d %d %d\n", f(1), f(2), f('a'), f(5));
    return 0;
}
```

`f(1)` sets `r` to 10 and falls into `case 2`, which adds 3: 13.

**Notes.**

* Two labels may stand together to share one set of statements: `case 'a': case 'e': ...`.
* A `case` may be inside a nested block of the `switch` (the shape known as Duff's device is allowed).

**Errors.**

| Mistake | What happens |
|---|---|
| `case` outside a `switch` | `ERROR 74: MISPLACED CASE` |
| the same value twice in one `switch` | `ERROR 75: DUPLICATE CASE` |
| a label that is not a constant (`case x:`) | `ERROR 50: CONSTANT REQUIRED` |
| a floating label | `ERROR 50: CONSTANT REQUIRED` |

```c
// expect: error E_CASE 4
int main(void)
{
    case 1: return 0;
}
```

**See also** `switch`, `default`, `break`, `enum`.

---

## Casts

`(` *type* `)` *expression* -- **operator**

Converts the value of the expression to the type in the brackets. A cast between integer types keeps the low bits (to `char`, the low 8; from `char` the value is extended with zeros, from `signed char` with the sign) and so can lose information. A cast to a floating type is exact for any `int` or `unsigned`; a cast of a floating value to an integer type cuts off the fraction, toward zero.

```c
// expect: exit 0
// screen: 0 52 3 65535
// screen: 1 3.5 2 -2
int main(void)
{
    int i = 0x1234, n = 7;
    cls();
    printf("%d %d %u\n", (char)i, n / 2, (unsigned)-1);
    printf("%.1f %d %d\n", (float)n / 2, (int)2.9, (int)-2.9);
    return 0;
}
```

`n / 2` is an integer division and gives 3, but `(float)n / 2` makes the division floating: 3.5.

**Notes.**

* Between integer and pointer types a cast is allowed: `(char *)p`, `(unsigned)p`, `(int *)a`. A pointer of one type can be converted to another only with a cast, except to and from `void *`.
* A floating value converted to an integer type keeps the low 16 bits of its integer part (8 for `char`); a value too big for the type gives no error.
* A floating type and a pointer type cannot be converted into each other, even with a cast.
* A cast binds more tightly than `* / %` and more loosely than the postfix operators: `(float)n / 2` casts `n` only.

**Errors.**

| Mistake | What happens |
|---|---|
| a cast between a floating type and a pointer | a compile error |

**See also** `sizeof`, `float`, `unsigned`, [Conversions](05_concepts.md#conversions), [Pointers](05_concepts.md#pointers).

---

## char

`char` -- **keyword**

A type of one byte. **`char` is unsigned**: it holds 0 to 255, and `char c = 255;` stays 255. `signed char` holds -128 to 127 and is extended with its sign when it is used in an expression; `unsigned char` is the same as `char`. Character constants such as `'A'` give the character's code.

```c
// expect: exit 0
// screen: 0 255 -1 65
// screen: 1 0
int main(void)
{
    char c = 255;
    signed char s = 255;
    cls();
    printf("%d %d %d\n", c, s, 'A');
    c = c + 1;
    printf("%d\n", c);
    return 0;
}
```

Adding 1 to 255 gives 256, which does not fit in a byte: the stored value is 0.

**Notes.**

* A `char` in an expression becomes an `int` first. A string is an array of `char` ending in a zero byte (see [Strings](05_concepts.md#strings)).
* `char` arrays are the usual buffers: `char buf[11];`.
* This differs from many C compilers, where plain `char` may be signed (see [Differences from standard C](05_concepts.md#differences-from-standard-c)).

**See also** `signed`, `unsigned`, `int`, [Characters](05_concepts.md#characters), [Strings](05_concepts.md#strings).

---

## Comma operator

*expression* `,` *expression* -- **operator**

Works out the left expression, throws its value away, then works out the right one, and gives its value. It has the lowest precedence of all, so it usually needs brackets.

```c
// expect: exit 43
int main(void)
{
    int n, a;
    a = (n = 3, n + 1);
    return a * 10 + n;
}
```

`n` is set to 3, then `n + 1` is 4, which is stored in `a`: the result is 4 x 10 + 3.

**Notes.**

* The commas that separate the arguments of a call, the items of a declaration and the elements of an initialiser are **not** the comma operator. To use the operator as an argument, bracket it: `f((a, b))` passes one value.
* The `for` statement uses it to run two things at once: `for (i = 0, n = 1; ...; i++, n *= 2)`.

**See also** `for`, `Operator precedence`, [Expressions](05_concepts.md#expressions).

---

## Comparison operators

`==` `!=` `<` `>` `<=` `>=` -- **operator**

Compare two values. The answer is an `int`: 1 when the comparison holds, 0 when it does not.

```c
// expect: exit 0
// screen: 0 1 0 1 0
int main(void)
{
    int a = -1;
    unsigned u = 1;
    cls();
    printf("%d %d %d %d\n", a < 1, a < u, 3 == 3, 'a' != 97);
    return 0;
}
```

`a < u` is 0: when one operand is `unsigned`, both are, so -1 becomes 65535, which is not less than 1.

**Notes.**

* The comparison is signed or unsigned according to the converted type of the operands.
* Pointers of the same type can be compared; so can a pointer with `0`.
* Floating values are compared exactly. Decimal fractions such as 0.1 are not exact in binary, so test floating results against a tolerance and not with `==`.
* `=` and `==` are different: `if (x = 3)` assigns.

**See also** `Logical operators`, `Conditional operator`, `if`, [Expressions](05_concepts.md#expressions).

---

## Conditional operator

*test* `?` *a* `:` *b* -- **operator**

If *test* is not zero, the value is *a*; otherwise it is *b*. Only the one chosen is worked out. It groups from the right, so `x ? 1 : y ? 2 : 3` is `x ? 1 : (y ? 2 : 3)`.

```c
// expect: exit 0
// screen: 0 7 3 1.0
int main(void)
{
    int a = 7, b = 3, k = 1;
    cls();
    printf("%d %d %.1f\n", a > b ? a : b, a == b ? 1 : a < b ? 2 : 3, k ? 1 : 0.5);
    return 0;
}
```

**Notes.**

* If one of *a* and *b* is floating and the other an integer, the integer is converted, so `k ? 1 : 0.5` is a floating 1.0 (the last item above).
* A pointer or `void` operand together with a floating one is `ERROR 40: TYPE MISMATCH`.

**See also** `if`, `Logical operators`, [Expressions](05_concepts.md#expressions).

---

## const

`const` *type* *name* -- **keyword**

Marks an object whose value is not to be changed: `const int limit = 20;`. Assigning to it afterwards, or adding to it with `++`, is a compile error.

```c
// expect: exit 20
const int limit = 20;
int main(void)
{
    return limit;
}
```

**Notes.**

* `const` is checked only for a direct assignment to the object. It does not place the data in ROM, and the `const` in `const char *p` or after the `*` is accepted but does not stop the pointer or what it points to from changing.
* A `const` array or structure counts its elements and members as constant.

**Errors.**

| Mistake | What happens |
|---|---|
| `=`, `+=`, `++` and so on applied to a `const` object | `ERROR 54: ASSIGNMENT TO CONST` |

```c
// expect: error E_CONST 5
const int limit = 20;
int main(void)
{
    limit = 30;
    return 0;
}
```

**See also** `static`, `enum`, [Types](05_concepts.md#types).

---

## continue

`continue;` -- **keyword**

Skips the rest of the body of the nearest enclosing loop and goes on with the next time round: in a `for`, to the step; in a `while` or `do`, to the test.

```c
// expect: exit 25
int main(void)
{
    int i, sum = 0;
    for (i = 1; i <= 10; i++) {
        if (i % 2 == 0)
            continue;
        sum += i;
    }
    return sum;
}
```

The even numbers are skipped; the program adds 1 + 3 + 5 + 7 + 9.

**Errors.**

| Mistake | What happens |
|---|---|
| `continue` outside a loop, even inside a `switch` | `ERROR 73: MISPLACED CONTINUE` |

```c
// expect: error E_CONTINUE 4
int main(void)
{
    continue;
    return 0;
}
```

**See also** `break`, `for`, `while`, `do`.

---

## default

`default:` -- **keyword**

The label in a `switch` that is taken when no `case` matches. It may stand anywhere among the cases, not only last. Without a `default`, a value that matches nothing skips the whole `switch`.

```c
// expect: exit 2
int main(void)
{
    int k = 7, r = 0;
    switch (k) {
    case 1: r = 1; break;
    default: r = 2;
    }
    return r;
}
```

**Errors.**

| Mistake | What happens |
|---|---|
| `default` outside a `switch` | `ERROR 74: MISPLACED CASE` |
| a second `default` in one `switch` | `ERROR 75: DUPLICATE CASE` |

**See also** `switch`, `case`, `break`.

---

## #define

`#define` *NAME* *replacement*, `#define` *NAME* -- **directive**

Makes *NAME* a **macro**: wherever it is used later in the program, the compiler puts the replacement text in its place. The replacement is the rest of the line; it may be empty. The commonest use is naming a constant.

```c
// expect: exit 12
#define W 4
#define H (W - 1)
#define AREA (W * H)
int main(void)
{
    return AREA;
}
```

**Notes.**

* A directive is a `#` that is the first thing on its line. It may stand anywhere a line may: between functions, or inside one. A `#` on a line by itself is ignored.
* The replacement can be any tokens, not only numbers: `#define LOOP for (i = 0; i < 3; i++)` or `#define RET return`. It is checked for lexical errors when the `#define` is read, and expanded where the name is used. Macros may use other macros, up to 8 deep.
* A macro's own name inside its expansion is left alone: `#define x (x + 1)` makes `x` mean "the variable x, plus one" and does not repeat for ever.
* **Only object-like macros exist.** A macro with arguments, `#define SQ(x) ((x) * (x))`, is not supported; write a function instead.
* A keyword cannot be the name of a macro.
* **A name can be defined only once.** Defining it a second time is an error, even with the same text (C allows that; Leap-C does not). Remove the first with `#undef`.
* The tokens of one expansion, nested ones included, are limited to 255.

**Errors.**

| Mistake | What happens |
|---|---|
| a name defined twice | `ERROR 22: ALREADY DEFINED` |
| a macro with arguments | `ERROR 1: NOT SUPPORTED` |
| no name, a number or a keyword as the name | `ERROR 20: SYNTAX ERROR` |
| a character that is not C in the replacement | `ERROR 10: BAD CHARACTER` |
| macros nested more than 8 deep, or an expansion of more than 255 tokens | `ERROR 90: NESTING TOO DEEP` |

```c
// expect: error E_REDEF 3
#define A 1
#define A 2
int main(void) { return 0; }
```

```c
// expect: error E_NOTSUP 2
#define SQ(x) ((x) * (x))
int main(void) { return 0; }
```

**See also** `#undef`, `#include`, `enum`, [The preprocessor](05_concepts.md#the-preprocessor), [Names](05_concepts.md#names).

---

## do

`do` *statement* `while (` *expression* `);` -- **keyword**

Repeats the statement, then tests the expression, and goes round again while it is not zero. Because the test comes after the body, the body always runs **at least once**.

```c
// expect: exit 6
int main(void)
{
    int n = 3, sum = 0;
    do {
        sum += n;
        n--;
    } while (n > 0);
    return sum;
}
```

The program adds 3 + 2 + 1.

**Notes.**

* The `;` after the closing bracket is part of the statement.
* `break` leaves a `do` loop; `continue` goes to its test.

**Errors.**

| Mistake | What happens |
|---|---|
| `do` without its `while` | `ERROR 20: SYNTAX ERROR` |

```c
// expect: error E_SYNTAX 6
int main(void)
{
    int x;
    do x = 1;
    return 0;
}
```

**See also** `while`, `for`, `break`, `continue`.

---

## double

`double` -- **keyword**

The same type as `float`: there is only one floating type in Leap-C, the 5-byte format of the TS2068's own ROM. `double` is accepted so that programs written for other compilers keep working, and `sizeof(double)` is 5.

```c
// expect: exit 5
int main(void)
{
    double d = 1.5;
    return sizeof(double);
}
```

`long double` is not supported (`ERROR 1: NOT SUPPORTED`).

**See also** `float`, `long`, [Floating point](05_concepts.md#floating-point).

---

## else

`if (` *expression* `)` *statement* `else` *statement* -- **keyword**

The part of an `if` statement that is done when the test is false. An `else` belongs to the **nearest** `if` that has none.

```c
// expect: exit 12
int t(int a, int b)
{
    int r;
    r = 0;
    if (a)
        if (b) r = 1;
        else r = 2;
    return r;
}
int main(void) { return t(1, 1) * 10 + t(1, 0) + t(0, 1) + t(0, 0); }
```

The `else` goes with `if (b)`, whatever the indentation says: `t(1, 1)` is 1, `t(1, 0)` is 2, and `t(0, 1)` and `t(0, 0)` are 0. Put the inner `if` in braces to change that.

**See also** `if`.

---

## enum

`enum` *tag* `{` *name* [`=` *constant*] `,` ... `}` -- **keyword**

Declares a set of named whole-number constants. The first name is 0, and each next one is one more than the one before, unless it is given a value with `=`, which restarts the count. A comma may follow the last name. The names are of type `int`; a variable of an `enum` type is an `int` too (2 bytes).

```c
// expect: exit 12
enum colour { RED, GREEN, BLUE = 10, CYAN };
int main(void)
{
    enum colour c = CYAN;
    return c + GREEN;
}
```

`RED` is 0, `GREEN` 1, `BLUE` 10 and `CYAN` 11; the program returns 11 + 1.

**Notes.**

* The tag may be left out: `enum { OFF, ON };` just defines the constants.
* An `enum` constant is a constant expression: it can size an array, label a `case`, or be the value of another constant.
* Enumeration constants share their name space with variables: a variable and a constant of the same name in one scope are an error.

**Errors.**

| Mistake | What happens |
|---|---|
| the same `enum` tag defined twice | `ERROR 22: ALREADY DEFINED` |
| a constant with the same name as a variable in the same scope | `ERROR 21: REDECLARED` |

**See also** `case`, `typedef`, `#define`, [Types](05_concepts.md#types).

---

## extern

`extern` *declaration* -- **keyword**

Declares an object or function that is defined elsewhere, without making room for it. Use it to name a variable that a function needs before the variable is defined.

```c
// expect: exit 9
extern int total;
int bump(void)
{
    total = total + 4;
    return total;
}
int total = 5;
int main(void)
{
    return bump();
}
```

**Notes.**

* Leap-C compiles **one source file only**, so `extern` can refer only to something defined later in the same program.
* `extern int a[];` declares an array whose size is given by its later definition.

**Errors.**

| Mistake | What happens |
|---|---|
| `extern` together with another storage class | `ERROR 26: BAD STORAGE CLASS` |

**See also** `static`, [Programs](05_concepts.md#programs), [Memory](05_concepts.md#memory).

---

## float

`float` -- **keyword**

A number with a fraction. `float` and `double` are the same type: the 5-byte floating format of the TS2068 ROM, with about 9.6 significant digits and magnitudes up to about 1.7E38. It is **not** IEEE. Whole numbers convert to `float` exactly; a `float` converted to an integer loses its fraction, toward zero.

```c
// expect: exit 5
// screen: 0 0.31 7 -2
int main(void)
{
    float x = 2.5;
    int n = x * 3;
    cls();
    printf("%.2f %d %d\n", x / 8, n, (int)-x);
    return sizeof(float);
}
```

`x * 3` is 7.5, and storing it in an `int` cuts it to 7.

**Notes.**

* Floating constants have a point, an exponent, or both: `1.5`, `.5`, `2.`, `1e5`, `2.5E-3`. A suffix `f`, `F`, `l` or `L` is accepted and means nothing.
* `printf("%f")` prints 6 decimals; `%.Nf` prints *N* (0 to 9). There is no `%e` or `%g`.
* There is no maths library (`sqrt`, `sin`): such functions are short to write in C (see [Part 7](07_examples.md)).
* A floating overflow, or a floating division by zero, stops the program with run-time error 6, `NUMBER TOO BIG`.
* A `float` object takes 5 bytes, and arithmetic is much slower than on integers.
* `% << >> & | ^ ~` do not work on floating values.

**Errors.**

| Mistake | What happens |
|---|---|
| a constant that is too big, in the source (`1e39`) | `ERROR 16: NUMBER TOO LARGE` |
| a malformed constant (`1e`, `1.5ff`, `1..2`) | `ERROR 15: BAD NUMBER` |
| a floating array size or `case` label | `ERROR 50: CONSTANT REQUIRED` |
| a floating `switch` value | `ERROR 51: BAD OPERAND TYPE` |

**See also** `double`, `Casts`, `int`, [Floating point](05_concepts.md#floating-point), [Numbers](05_concepts.md#numbers).

---

## for

`for (` *start* `;` *test* `;` *step* `)` *statement* -- **keyword**

A counting loop. *start* is done once. Then, before each time round, *test* is tried: if it is zero the loop ends. After each time round *step* is done. Any of the three parts may be left out; a missing *test* counts as true.

```c
// expect: exit 32
// screen: 0 1 2 4 8 16
int main(void)
{
    int i, n;
    cls();
    for (i = 0, n = 1; i < 5; i++, n *= 2)
        printf("%d ", n);
    return n;
}
```

The comma operator runs two things in the start and in the step. After the fifth time round `n` has been doubled to 32.

**Notes.**

* `for (;;)` goes on for ever, until a `break` or `return`.
* C89 has no declaration inside the brackets: declare the counter before the loop.
* `break` leaves the loop; `continue` goes to the *step*.

**See also** `while`, `do`, `break`, `continue`, `Comma operator`.

---

## FREE

`FREE` -- **command**

Shows how much memory is left. It reports two lines in the status colours at the bottom of the screen, until you press a key:

```
SOURCE s B  FREE f B
IMAGE i B  HEAP h B
```

`SOURCE` is the size of your program in the line store and `FREE` the room left for it. `IMAGE` is the size of the last program that compiled successfully (0 before any), and `HEAP` the largest block that `malloc` could return to a program with the source as it is now.

```
FREE
```

The program is shown as it was when you press a key.

**Notes.**

* The source can be about 18 KB; a typical program of 850 lines fits. The heap is up to about 18 KB with a small program, and less as the source grows.
* `RUN` ends with the same `IMAGE` and `HEAP` figures.

**See also** `RUN`, `NEW`, [Memory](05_concepts.md#memory), [Appendix E](08_appendices.md) (limits).

---

## goto

`goto` *label* `;` -- **keyword**

Continues the program at *label*, which is a name followed by a colon at the start of a statement, in the same function. It can jump forward or back, and out of loops and blocks.

```c
// expect: exit 5
int main(void)
{
    int n = 0;
again:
    n++;
    if (n < 5)
        goto again;
    return n;
}
```

**Notes.**

* Labels have a name space of their own: a label and a variable may have the same name.
* A label belongs to its function: you cannot jump to another function's label.
* `goto` is the way out of several loops at once; elsewhere a loop with `break` and `continue` is clearer.

**Errors.**

| Mistake | What happens |
|---|---|
| a `goto` to a label the function does not define (reported at the first such `goto`) | `ERROR 76: UNDEFINED LABEL`, and the label's name is shown |
| the same label twice in one function | `ERROR 22: ALREADY DEFINED` |
| a number instead of a name (`goto 5`) | `ERROR 20: SYNTAX ERROR` |

```c
// expect: error E_UNDEFLABEL 4
int main(void)
{
    goto nowhere;
    return 0;
}
```

**See also** `break`, `continue`, `return`, [Programs](05_concepts.md#programs).

---

## if

`if (` *expression* `)` *statement*, `if (` *expression* `)` *statement* `else` *statement* -- **keyword**

Does the statement when the expression is not zero. With an `else`, does the second statement when it is zero. `if` statements can follow `else` to make a chain.

```c
// expect: exit 2
int sign(int n)
{
    if (n < 0)
        return -1;
    else if (n == 0)
        return 0;
    else
        return 1;
}
int main(void)
{
    return sign(-5) + sign(0) + sign(9) + 2;
}
```

**Notes.**

* The expression may be any number or pointer: 0 is false and anything else is true.
* Use `{ }` to put several statements under one `if`.
* The expression must be a simple value: a structure or a `void` value cannot be tested.

**Errors.**

| Mistake | What happens |
|---|---|
| an `else` with no `if` | `ERROR 20: SYNTAX ERROR` |
| a structure or a `void` call as the test | `ERROR 51: BAD OPERAND TYPE` |

```c
// expect: error E_SYNTAX 5
int main(void)
{
    int x;
    else x = 1;
    return 0;
}
```

**See also** `else`, `switch`, `Conditional operator`, `Comparison operators`, `Logical operators`.

---

## #if and the other unsupported directives

`#if`, `#ifdef`, `#ifndef`, `#elif`, `#else`, `#endif`, `#error`, `#line`, ... -- **directive** (not supported)

Leap-C has four directives: `#define`, `#undef`, `#include` and `#pragma hires`. **Any other directive** stops the compile with `ERROR 1: NOT SUPPORTED`, at the line of the directive. This includes the conditional compilation family (`#if`, `#ifdef`, `#ifndef`, `#elif`, `#else`, `#endif`), `#error` and `#line`. So does any `#pragma` other than `#pragma hires`, a `#define` with arguments, and an `#include` of any file but `leap.h`.

```c
// expect: error E_NOTSUP 2
#if 1
int main(void) { return 0; }
```

```c
// expect: error E_NOTSUP 3
int x;
#ifdef X
int main(void) { return 0; }
```

**Notes.**

* Conditional compilation is rarely wanted in a program that is a single file; to switch a part of a program off, put it inside `/* ... */` (the comment does not nest) or `//`.

**See also** `#define`, `#include`, `#pragma`, [The preprocessor](05_concepts.md#the-preprocessor).

---

## #include

`#include <leap.h>`, `#include "leap.h"` -- **directive**

Accepted, and does nothing. The library (`printf`, `plot`, `malloc` and the rest) is built into the ROM, so there is no header to include; the directive exists so that programs written for other C systems keep compiling.

```c
// expect: exit 0
// screen: 0 no include needed
#include <leap.h>
int main(void)
{
    cls();
    puts("no include needed");
    return 0;
}
```

**Notes.**

* The same program without the first line is just as good.
* Nothing may follow the closing `>` or `"` on the line.

**Errors.**

| Mistake | What happens |
|---|---|
| `#include` of any other file (`<stdio.h>`) | `ERROR 1: NOT SUPPORTED` |
| something after the file name | `ERROR 20: SYNTAX ERROR` |

```c
// expect: error E_NOTSUP 2
#include <stdio.h>
int main(void) { return 0; }
```

**See also** `#define`, [The preprocessor](05_concepts.md#the-preprocessor), [Part 4](04_library.md).

---

## Increment and decrement

`++` `--` -- **operator**

`++x` adds 1 to `x` and gives the new value; `x++` adds 1 and gives the **old** value. `--x` and `x--` take 1 away in the same way.

```c
// expect: exit 0
// screen: 0 5 7 7
// screen: 1 20 2.5
int a[3] = { 10, 20, 30 };
int main(void)
{
    int i = 5, j, k;
    int *p;
    float f = 1.5;
    j = i++;
    k = ++i;
    p = a;
    p++;
    f++;
    cls();
    printf("%d %d %d\n", j, i, k);
    printf("%d %.1f\n", *p, f);
    return 0;
}
```

`j = i++` stores 5 and leaves `i` at 6; `k = ++i` makes `i` 7 and stores 7.

**Notes.**

* On a pointer, `++` moves by one **element**: `p++` for an `int *` adds 2 to the address.
* The operand must be an lvalue (something that can be assigned to). `*p++` takes what `p` points to, then moves `p`.
* `++` and `--` work on floating values as well.

**Errors.**

| Mistake | What happens |
|---|---|
| `++5`, `(a + b)++` | `ERROR 53: NOT AN LVALUE` |
| `++` or `--` on a `const` object | `ERROR 54: ASSIGNMENT TO CONST` |

```c
// expect: error E_LVALUE 4
int main(void)
{
    return ++5;
}
```

**See also** `Assignment operators`, `Pointer and address operators`, [Pointers](05_concepts.md#pointers).

---

## int

`int` -- **keyword**

A whole number of 16 bits, from -32768 to 32767. It wraps around: `32767 + 1` is -32768. `short`, `short int`, `signed` and `signed int` are the same type; `unsigned` and `unsigned int` hold 0 to 65535. Where C allows the type to be left out, it is `int`: `static count;`, `const limit = 5;`, and a function defined as `main()`.

```c
// expect: exit 0
// screen: 0 32767 -32768 65535
int main(void)
{
    int big = 32767;
    unsigned u = 65535;
    cls();
    printf("%d %d %u\n", big, big + 1, u);
    return 0;
}
```

**Notes.**

* A constant is written in decimal, in hexadecimal with `0x`, or in octal with a leading `0`. Its value must be 0 to 65535; larger gives `ERROR 16: NUMBER TOO LARGE`. A suffix `u` or `U` is accepted; `l` and `L` are not supported.
* Division by zero gives 0 and not an error.

**Errors.**

| Mistake | What happens |
|---|---|
| contradictory words (`int char`, `signed unsigned`) | `ERROR 24: BAD TYPE SPECIFIERS` |

**See also** `short`, `signed`, `unsigned`, `long`, [Numbers](05_concepts.md#numbers), [Types](05_concepts.md#types).

---

## LIB

`LIB "name"`, `LIB ""`, `LIB` -- **command**

Loads a library of assembly-language functions from tape, or unloads the one that is loaded. `LIB "name"` loads the library with that name (1 to 10 characters); `LIB ""` loads the next library on the tape, whatever its name. `LIB` on its own unloads the library.

While the tape plays the status row shows `LOADING`, then `LOADING name` when the header is found. The report is shown on the bottom two rows until a key is pressed:

| First row | When |
|---|---|
| `LIBRARY name: n FUNCTIONS` | the library arrived whole: its name (as written on the tape) and the number of functions it adds |
| `BAD TAPE VERSION` | not a library for this ROM; nothing was written |
| `LOAD FAILED` | no such tape found within about 2 minutes, a library longer than 1 KB, or a bad block |
| `BREAK` | SPACE or BREAK stopped it |
| `BAD NAME` | more than 10 characters, no closing quote, or something after it |

The second row is `SOURCE s B  FREE f B`. `LIB` alone shows `NO LIBRARY` on the status row until a key is pressed.

```
LIB "shapes"
```

After the tape has played, the bottom rows read `LIBRARY shapes: 3 FUNCTIONS`; the program can then call `circle`, `box` and `isqrt` without declaring them.

**Notes.**

* **One library is loaded at a time.** `LIB "other"` replaces it.
* The library **stays** through `NEW`, `LOAD` and `RUN`: a program loaded from tape can use it at once. `LIB` alone unloads it, and a reset clears it.
* A loaded library occupies the 1 KB of program memory called image region 3, so the largest program you can compile is 1 KB smaller.
* If a failure writes into that region, no library is left loaded; any other failure keeps the library that was loaded before.
* Without the library, a call to one of its functions is `ERROR 70: UNDEFINED FUNCTION`.
* A library tape, a program tape and a data tape are different kinds: `LIB` skips program and data tapes, and `LOAD`, `VERIFY` and `tape_load` skip library tapes.

**See also** `LOAD`, `NEW`, [Part 6](06_libraries.md), [Tapes](05_concepts.md#tapes).

---

## LIST

`LIST` -- **command**

Shows the program a page (23 rows) at a time, with the keywords in bold. A line that does not fit on the page starts the next one. Press a key to see the next page; BREAK (CAPS SHIFT + SPACE) ends the listing.

```
LIST
```

**Notes.**

* A line longer than 32 characters wraps at its last space, onto up to four rows.
* `LIST` changes nothing. The editor itself shows up to 20 lines above the cursor's line.

**See also** `RUN`, `FREE`, [The editor](05_concepts.md#the-editor).

---

## LOAD

`LOAD "name"`, `LOAD ""` -- **command**

Reads a program from tape and puts it in the editor, **replacing** the program that is there. `LOAD "name"` loads the program with that name; `LOAD ""` loads the next program on the tape, whatever it is called. While the tape plays, the status row shows `LOADING` and, once the header is found, `LOADING name`.

Afterwards two rows are shown until a key is pressed:

| First row | When |
|---|---|
| `LOADED name` | the program arrived whole; the cursor is on the empty line after its last line |
| `LOAD FAILED` | no program tape found, or a bad block |
| `BAD TAPE VERSION` | the tape is not a Leap-C tape |
| `BREAK` | SPACE or BREAK stopped it |
| `BAD NAME` | more than 10 characters, no closing quote, or something after it |

The second row is `SOURCE s B  FREE f B`.

```
LOAD "hello"
```

**Notes.**

* A failed `LOAD` keeps your program, except when a longer program had already begun to replace it: then the program is empty, as after `NEW`. The same holds for BREAK in the middle of such a program.
* **`LOAD` skips data tapes** (the ones `tape_save` writes), and `tape_load` skips programs.
* Leap-C tapes carry their own version word. The TS2068's BASIC and Leap V2 refuse them, and Leap-C refuses theirs (`BAD TAPE VERSION`).
* The loaded library is not changed.
* `LOAD` is a command only on the empty last line: a line such as `load(x);` is ordinary source.

**See also** `SAVE`, `VERIFY`, `LIB`, `tape_load` in [Part 4](04_library.md#tape_load), [Tapes](05_concepts.md#tapes).

---

## Logical operators

`&&` `||` `!` -- **operator**

`a && b` is 1 if both are not zero, otherwise 0. `a || b` is 1 if either is not zero, otherwise 0. `!a` is 1 if `a` is zero, otherwise 0. The answer is always 0 or 1.

`&&` and `||` **stop as soon as the answer is known**: if `a` is false in `a && b`, or true in `a || b`, then `b` is not worked out at all. That makes guards safe: `p != 0 && *p > 3`.

```c
// expect: exit 0
// screen: 0 0 1 0
// screen: 1 2
int n;
int t(int v)
{
    n++;
    return v;
}
int main(void)
{
    cls();
    printf("%d %d %d\n", t(0) && t(1), t(1) || t(0), !5);
    printf("%d\n", n);
    return 0;
}
```

`t` is called only twice, once for each operator: the right-hand calls are skipped.

**Notes.**

* `&&` binds more tightly than `||`; both bind more loosely than the comparisons. So `a > 3 && a < 10` needs no brackets.
* Floating values may be used; a pointer is false when it is 0.
* These are not `&` and `|`, which work on bits (see `Bitwise operators`).

**See also** `Comparison operators`, `if`, `Bitwise operators`.

---

## long

`long` -- **keyword** (not supported)

Reserved, and gives `ERROR 1: NOT SUPPORTED`. There are no 32-bit integers in Leap-C: `int` is 16 bits. The same error is given by `long double`, and by a constant with the suffix `L` (`10L`, `1ul`).

```c
// expect: error E_NOTSUP 2
long total;
int main(void) { return 0; }
```

```c
// expect: error E_NOTSUP 4
int main(void)
{
    return 10L;
}
```

**Notes.**

* A constant above 65535 without a suffix is `ERROR 16: NUMBER TOO LARGE`.
* For a bigger range, use `unsigned` (0 to 65535), a pair of `int`s, or `float` (about 9.6 significant digits).

**See also** `int`, `unsigned`, `float`, `short`, [Numbers](05_concepts.md#numbers), [Differences from standard C](05_concepts.md#differences-from-standard-c).

---

## Member operators

*structure* `.` *member*, *pointer* `->` *member* -- **operator**

Pick one member out of a structure. `.` is used with the structure itself, `->` with a pointer to one: `p->v` means `(*p).v`. Members can be read, assigned to, and used with `&`.

```c
// expect: exit 12
struct node { int v; struct node *next; };
struct node a;
struct node b;
int main(void)
{
    struct node *p;
    a.v = 5;
    b.v = 7;
    a.next = &b;
    b.next = 0;
    p = &a;
    return p->v + p->next->v;
}
```

`p->next->v` goes to the next node and picks its `v`: 5 + 7.

**Notes.**

* A structure has no padding: its members follow one another byte by byte.
* A structure cannot be passed to a function, returned from one, or assigned as a whole; pass `&v`.
* `.` and `->` bind as tightly as anything in C, along with `[ ]` and `( )`.

**Errors.**

| Mistake | What happens |
|---|---|
| a name that is not a member | `ERROR 52: NO SUCH MEMBER`, and the name is shown |
| `.` or `->` on something that is not a structure | `ERROR 51: BAD OPERAND TYPE` |

```c
// expect: error E_MEMBER 6
struct s { int a; };
struct s v;
int main(void)
{
    return v.b;
}
```

**See also** `struct`, `Pointer and address operators`, [Structures](05_concepts.md#structures), [Pointers](05_concepts.md#pointers).

---

## NEW

`NEW` -- **command**

Clears the program, leaving the editor empty. Save the program first if you want to keep it.

```
NEW
```

The status row reads `LINE 1/0`: line 1 of a program of no lines.

**Notes.**

* A loaded library stays loaded.

**See also** `SAVE`, `LOAD`, `LIB`, [The editor](05_concepts.md#the-editor).

---

## Operator precedence

An expression is worked out in order of precedence: operators higher in the table bind more tightly. Operators on one row have the same precedence and group as shown.

| Precedence | Operators | Group |
|---|---|---|
| 1 (tightest) | `()` call, `[]`, `.`, `->`, postfix `++` `--` | left to right |
| 2 | prefix `++` `--`, `+` `-` (signs), `!`, `~`, `*` (indirection), `&` (address), `sizeof`, casts | right to left |
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
| 14 | `=` `+=` `-=` `*=` `/=` `%=` `&=` `^=` `\|=` `<<=` `>>=` | right to left |
| 15 (loosest) | `,` | left to right |

```c
// expect: exit 0
// screen: 0 14 8 0 3 1
int main(void)
{
    int a = 2, b = 3, c = 4;
    cls();
    printf("%d %d %d %d %d\n", a + b * c, 1 << a + 1, 6 & b == 3, 1 | a ^ b & c, a || b && 0);
    return 0;
}
```

* `a + b * c` is `a + (b * c)`: 14.
* `1 << a + 1` is `1 << (a + 1)`: 8.
* `6 & b == 3` is `6 & (b == 3)`: 6 & 1 is 0. This is the usual trap: write `(6 & b) == 3` when you mean that.
* `1 | a ^ b & c` is `1 | (a ^ (b & c))`: 3.
* `a || b && 0` is `a || (b && 0)`: 1.

**Notes.**

* When in doubt, use brackets; they cost nothing at run time.
* The sign `-` and `+`, `*` and `&` in front of one operand are in row 2; the same characters between two operands are in rows 3, 4 and 8.

**See also** `Arithmetic operators`, `Bitwise operators`, `Logical operators`, [Expressions](05_concepts.md#expressions).

---

## Pointer and address operators

`&`*lvalue*, `*`*pointer*, *pointer*`[`*index*`]` -- **operator**

`&x` gives the address of `x`: a pointer to it. `*p` is the object `p` points to (it can be read and assigned to). `p[i]` is `*(p + i)`. A pointer plus or minus an integer is moved by that many **elements**, not bytes. One pointer minus another of the same type gives the number of elements between them, as an `int`.

```c
// expect: exit 0
// screen: 0 30 3 20
// screen: 1 8
int a[4] = { 10, 20, 30, 40 };
int main(void)
{
    int *p, *q;
    int n = 5;
    p = a;
    q = &a[3];
    cls();
    printf("%d %d %d\n", *(p + 2), q - p, p[1]);
    p = &n;
    *p = 8;
    printf("%d\n", n);
    return 0;
}
```

The name of an array stands for the address of its first element, so `p = a` needs no `&`.

**Notes.**

* A pointer is 16 bits. `0` is the null pointer, and the only integer that can be stored in a pointer without a cast.
* **Nothing checks array bounds or null pointers.** `*p` with `p` equal to 0 reads address 0.
* `void *` can be stored in, and taken from, any object pointer without a cast. Other pointer types need one.
* `&` needs an object: `&5` and `&(x + 1)` are errors. `&` of an array element or member is fine.
* A pointer to a function is called like the function: see [Functions](05_concepts.md#functions).

**Errors.**

| Mistake | What happens |
|---|---|
| `*` of something that is not a pointer | `ERROR 51: BAD OPERAND TYPE` |
| `&` of something that is not an object | `ERROR 53: NOT AN LVALUE` |
| two pointers added | `ERROR 51: BAD OPERAND TYPE` |
| a pointer stored in an integer, or an integer other than 0 stored in a pointer, without a cast | `ERROR 40: TYPE MISMATCH` |

```c
// expect: error E_OPERAND 5
int main(void)
{
    int x = 3;
    return *x;
}
```

**See also** `Member operators`, `Increment and decrement`, `Casts`, `sizeof`, `void`, [Pointers](05_concepts.md#pointers), [Arrays](05_concepts.md#arrays).

---

## #pragma

`#pragma hires` -- **directive**

Keeps the compiled program out of the memory at `$6000-$77FF`, which the TS2068's high-resolution colour mode uses. A program that calls `mode(1)` should say so. The compiler fills that memory last, so only a large program reaches it; without the pragma, `mode(1)` in such a program stops it with run-time error 3, `HI-RES IN USE`.

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

**Notes.**

* `hires` is the only pragma. Its name is case-sensitive, and it is never replaced by a macro.
* It may be given more than once, and anywhere a directive may be, but it applies **from its line on**: what is already in that memory when the compiler reaches the pragma stays there. Put it first.
* Nothing else may follow `hires` on the line.
* With the pragma the room for the program is smaller by that memory, so a very large program may be `ERROR 101: PROGRAM TOO BIG`.

**Errors.**

| Mistake | What happens |
|---|---|
| any other pragma (`#pragma once`, `#pragma HIRES`), or none | `ERROR 1: NOT SUPPORTED` |
| anything after `hires` | `ERROR 20: SYNTAX ERROR` |
| a program that cannot fit once the memory is kept clear | `ERROR 101: PROGRAM TOO BIG` |

```c
// expect: error E_SYNTAX 2
#pragma hires please
int main(void) { return 0; }
```

**See also** `#define`, `mode` in [Part 4](04_library.md#mode), [High resolution](05_concepts.md#high-resolution), [Memory](05_concepts.md#memory).

---

## register

`register` *declaration* -- **keyword**

A storage-class word for a local variable that suggests it be kept in a register. It is accepted and **ignored**: the variable is an ordinary local.

```c
// expect: exit 10
int main(void)
{
    register int i;
    int sum = 0;
    for (i = 1; i <= 4; i++)
        sum += i;
    return sum;
}
```

**See also** `auto`, `static`, [Memory](05_concepts.md#memory).

---

## return

`return;`, `return` *expression* `;` -- **keyword**

Leaves the function at once. With an expression, it gives its value to the caller, converted to the function's type. A function of type `void` returns with `return;`, or by running off its closing brace.

```c
// expect: exit 30
int twice(int n)
{
    return n * 2;
}
void nothing(void)
{
    return;
}
int main(void)
{
    nothing();
    return twice(15);
}
```

**Notes.**

* **`main`'s value is the program's exit status**, shown as `EXIT n` after `RUN`. It is signed: `return -42;` shows `EXIT -42`. `void main(void)` shows `EXIT 0`. `exit(n)` in [Part 4](04_library.md#exit) ends the program from anywhere.
* A structure cannot be returned: return a pointer, or fill a structure that the caller passes by address.

**Errors.**

| Mistake | What happens |
|---|---|
| a value returned from a `void` function | `ERROR 40: TYPE MISMATCH` |
| a pointer returned from an `int` function | `ERROR 40: TYPE MISMATCH` |
| a structure returned | `ERROR 1: NOT SUPPORTED` |

**See also** `void`, `goto`, [Functions](05_concepts.md#functions), [Programs](05_concepts.md#programs).

---

## RUN

`RUN` -- **command**

Compiles the whole program and, if there is no error, runs it. The status row shows `COMPILING` while it compiles. Nothing runs if the compiler finds a mistake. When the program ends, whatever is on the screen stays, and two report rows appear at the bottom, in the status colours, until you press a key. The key is not typed; it returns you to the editor with the program as it was.

```
int main(void)
{
    cls();
    printf("Hello, TS2068!\n");
    return 0;
}
RUN
```

```
Hello, TS2068!

...
EXIT 0
IMAGE 39 B  HEAP 18340 B
```

`EXIT 0` is what `main` returned; `IMAGE` is the size of the compiled program and `HEAP` the memory `malloc` could have used.

| Outcome | First row | Second row |
|---|---|---|
| the program ends | `EXIT n` (`main`'s value, or `exit()`'s; signed) | `IMAGE i B  HEAP h B` |
| compile error | `ERROR n: MESSAGE` | `LINE m` |
| run-time error | `RUNTIME ERROR n: MESSAGE` | `LINE m` |
| BREAK pressed | `BREAK` | `LINE m` |

**Notes.**

* **A compile error.** The compile stops at the first error. For an undeclared, undefined or duplicated name, the second row also shows the name, `LINE 5  'cont'`. When you press a key the editor shows line *m* with the cursor **at the place where the compiler stopped**; for a missing `;` that is the end of the line that lacks it. Line numbers count from 1.
* **A run-time error** shows the message over what the program printed; the line is where the function that failed **starts** (its first line), and the cursor goes there.
* **BREAK** (CAPS SHIFT + SPACE) stops any running program. The report is `BREAK` and `LINE m`.
* A program starts with the screen as the editor left it: call `cls()` first if it prints.
* The messages are listed in [Appendix A](08_appendices.md), [B](08_appendices.md) and [C](08_appendices.md).
* **After a report, press a key once every key is up**: Leap-C ignores a key still held from the command, so a report cannot vanish before you read it.

**Errors.** See `RUN`'s table above; for the messages themselves see [Errors](05_concepts.md#errors).

**See also** `LIST`, `NEW`, `FREE`, [Programs](05_concepts.md#programs), [BREAK](05_concepts.md#break).

---

## SAVE

`SAVE "name"` -- **command**

Writes the program (its source) to tape. *name* is 1 to 10 characters. While the tape moves, the status row shows `SAVING name`. Afterwards two rows are shown until a key is pressed:

| First row | When |
|---|---|
| `SAVED name` | the program was written |
| `BREAK` | SPACE or BREAK stopped it; no data block follows |
| `BAD NAME` | no name, more than 10 characters, no closing quote, or something after it |
| `NO PROGRAM` | the program is empty: nothing to save |

The second row is `SOURCE s B  FREE f B`.

```
SAVE "hello"
```

The report reads `SAVED hello`.

**Notes.**

* The word `SAVE`, in any case, followed by spaces (or none) and a quote makes the command. `SAVE` alone, or `save(x);`, is ordinary source.
* Only the source is saved, not the compiled program or any data. A program's own data are written by `tape_save` in [Part 4](04_library.md#tape_save).
* On a PC, `tools/c2tape.py` makes a tape from a `.c` file (see `docs/EMULATORS.md` in the repository).
* Leap-C tapes carry their own version word; the TS2068's BASIC and Leap V2 refuse them.

**See also** `LOAD`, `VERIFY`, `NEW`, [Tapes](05_concepts.md#tapes).

---

## short

`short` -- **keyword**

The same as `int`: 16 bits, from -32768 to 32767. `short int`, `signed short` and `unsigned short` are accepted; `unsigned short` is `unsigned`.

```c
// expect: exit 2
// screen: 0 -32768
int main(void)
{
    short s = 32767;
    cls();
    s = s + 1;
    printf("%d\n", s);
    return sizeof(short);
}
```

**See also** `int`, `unsigned`, `signed`, `long`, [Types](05_concepts.md#types).

---

## signed

`signed` -- **keyword**

`signed char` is a one-byte number from -128 to 127: it is extended with its sign when used in an expression. `signed` alone, or `signed int`, is the same as `int`.

```c
// expect: exit 0
// screen: 0 -128 -1 255
int main(void)
{
    signed char a = 128, b = 255;
    unsigned char c = b;
    cls();
    printf("%d %d %d\n", a, b, c);
    return 0;
}
```

The byte 255 is -1 as a `signed char` and 255 as an `unsigned char`.

**Errors.**

| Mistake | What happens |
|---|---|
| `signed unsigned` | `ERROR 24: BAD TYPE SPECIFIERS` |

**See also** `char`, `unsigned`, `int`, [Characters](05_concepts.md#characters), [Types](05_concepts.md#types).

---

## sizeof

`sizeof (` *type* `)`, `sizeof` *expression* -- **keyword** and **operator**

The size in bytes of a type, or of the type of an expression. The result is an `unsigned`, fixed when the program is compiled: **the expression is not worked out**, so `sizeof x++` leaves `x` as it was and `sizeof(f())` does not call `f`.

| Type | Size |
|---|---|
| `char`, `signed char`, `unsigned char` | 1 |
| `int`, `short`, `unsigned`, `enum`, any pointer | 2 |
| `float`, `double` | 5 |
| an array | the number of elements times the size of one |
| a `struct` | the sum of its members (no padding) |

```c
// expect: exit 0
// screen: 0 1 2 5 2 20
// screen: 1 3 10
struct pair { int a; char b; };
int table[10];
int main(void)
{
    cls();
    printf("%u %u %u %u %u\n", sizeof(char), sizeof(int), sizeof(float), sizeof(char *), sizeof table);
    printf("%u %u\n", sizeof(struct pair), sizeof table / sizeof table[0]);
    return 0;
}
```

`sizeof table / sizeof table[0]` is the number of elements.

**Notes.**

* Brackets are needed around a type name, not around an expression.
* `sizeof` is a constant expression: it can size an array.

**Errors.**

| Mistake | What happens |
|---|---|
| `sizeof` of a `void` value or of a function | `ERROR 41: INCOMPLETE TYPE` |
| `sizeof` of a structure that is not yet defined | `ERROR 41: INCOMPLETE TYPE` |

**See also** `Casts`, `struct`, `malloc` in [Part 4](04_library.md#malloc), [Arrays](05_concepts.md#arrays), [Types](05_concepts.md#types).

---

## static

`static` *declaration* -- **keyword**

Inside a function, makes a variable that **keeps its value** between calls: it is made once, set to 0 or to its initialiser when the program starts, and never goes away. Outside any function, `static` makes a name private to the file; since a Leap-C program is one file, that changes nothing.

```c
// expect: exit 3
int count(void)
{
    static int n;
    n++;
    return n;
}
int main(void)
{
    count();
    count();
    return count();
}
```

**Notes.**

* A `static` local is the way to have a big local array: ordinary locals are limited to 255 bytes in a function.
* A `static` array or structure may have an initialiser (`static char *names[2] = { "x" };`); an ordinary local array or structure may not (see [Differences from standard C](05_concepts.md#differences-from-standard-c)).
* Initialisers of static objects must be constants.

**Errors.**

| Mistake | What happens |
|---|---|
| `static` with another storage class, or on a parameter or a structure member | `ERROR 26: BAD STORAGE CLASS` |
| a `static` function declared inside a function | `ERROR 26: BAD STORAGE CLASS` |
| an initialiser that is not constant | `ERROR 50: CONSTANT REQUIRED` |

```c
// expect: error E_STORAGE 3
void f(void) {
  static int g(void);
}
```

**See also** `auto`, `extern`, `const`, [Memory](05_concepts.md#memory), [Names](05_concepts.md#names).

---

## struct

`struct` *tag* `{` *member* `;` ... `}`, `struct` *tag* *variable* -- **keyword**

Groups several named members into one object. The members follow one another in memory with **no padding**; the size is the sum of the sizes. A member may be of any type that is complete, including an array or another structure. A structure may hold a pointer to itself.

```c
// expect: exit 0
// screen: 0 7 9 16
struct point { int x; int y; };
void move(struct point *p, int dx)
{
    p->x += dx;
}
int main(void)
{
    struct point a;
    a.x = 4;
    a.y = 9;
    move(&a, 3);
    cls();
    printf("%d %d %d\n", a.x, a.y, a.x + a.y);
    return 0;
}
```

**Notes.**

* Members are picked out with `.` and `->` (see `Member operators`).
* `typedef` gives a structure a short name: `typedef struct node { int v; struct node *next; } Node;`.
* **Not supported:** a structure as a parameter or as a return value, the assignment of one structure to another, bit fields, and an initialiser on a local structure. Use pointers and `memcpy`, and make the structure `static`, or assign its members.
* A static structure may have an initialiser, in braces, with the inner braces optional.

**Errors.**

| Mistake | What happens |
|---|---|
| a structure assigned to another | `ERROR 1: NOT SUPPORTED` |
| a structure parameter or return value, a bit field | `ERROR 1: NOT SUPPORTED` |
| `struct s { };`, a structure with no members | `ERROR 20: SYNTAX ERROR` |
| the same tag defined twice | `ERROR 22: ALREADY DEFINED` |
| an object of a structure that is not defined | `ERROR 41: INCOMPLETE TYPE` |

```c
// expect: error E_NOTSUP 7
struct s { int a; };
struct s v;
struct s w;
int main(void)
{
    v = w;
    return 0;
}
```

**See also** `Member operators`, `typedef`, `sizeof`, [Structures](05_concepts.md#structures), [Types](05_concepts.md#types).

---

## switch

`switch (` *expression* `) {` ... `}` -- **keyword**

Chooses among several alternatives by the value of an integer or a `char`. The program jumps to the `case` label whose constant equals the value, or to `default` if none does, and carries on from there until a `break`.

```c
// expect: exit 0
// screen: 0 vowel
// screen: 1 space
// screen: 2 other
void show(int c)
{
    switch (c) {
    case 'a': case 'e': case 'i': case 'o': case 'u':
        puts("vowel");
        break;
    case ' ':
        puts("space");
        break;
    default:
        puts("other");
    }
}
int main(void)
{
    cls();
    show('e');
    show(' ');
    show('x');
    return 0;
}
```

**Notes.**

* The expression may be an `int`, an `unsigned` or a `char`; the labels are compared as the converted type. A `char` or an `unsigned` value above 32767 can be a label.
* The number of cases is limited only by memory.
* `continue` inside a `switch` belongs to the loop around it.

**Errors.**

| Mistake | What happens |
|---|---|
| a pointer, a structure or a floating value as the expression | `ERROR 51: BAD OPERAND TYPE` |
| the same value in two labels, or two `default`s | `ERROR 75: DUPLICATE CASE` |
| a label that is not constant | `ERROR 50: CONSTANT REQUIRED` |

```c
// expect: error E_DUPCASE 6
int main(void)
{
    switch (1) {
    case 1: ;
    case 1: ;
    }
    return 0;
}
```

**See also** `case`, `default`, `break`, `if`, `enum`.

---

## typedef

`typedef` *type* *name* `;` -- **keyword**

Gives a new name to a type. After `typedef unsigned word;` the word `word` can be used wherever `unsigned` could. It works for any type: pointers, arrays, structures, pointers to functions.

```c
// expect: exit 7
// screen: 0 3,4 65535
typedef unsigned word;
typedef struct point { int x; int y; } Point;
int main(void)
{
    Point p;
    word w = 0;
    p.x = 3;
    p.y = 4;
    cls();
    printf("%d,%d %u\n", p.x, p.y, w - 1);
    return p.x + p.y;
}
```

**Notes.**

* A `typedef` name follows the rules of other names: it can be declared in a block and shadows an outer name there.
* It may not have an initialiser: `typedef int t = 3;` is an error.

**Errors.**

| Mistake | What happens |
|---|---|
| `typedef` with an initialiser | `ERROR 28: BAD INITIALISER` |
| the same `typedef` name declared twice in one scope | `ERROR 21: REDECLARED` |

**See also** `struct`, `enum`, `#define`, [Types](05_concepts.md#types), [Names](05_concepts.md#names).

---

## #undef

`#undef` *NAME* -- **directive**

Removes the definition of the macro *NAME*, so that it may be defined again, with other text. If *NAME* is not defined, nothing happens.

```c
// expect: exit 9
#define N 4
#undef N
#define N 9
int main(void) { return N; }
```

**Notes.**

* This is the only way to change a macro, because defining one twice is an error.
* The directive may stand anywhere, including inside a function, to give a name a short life.

**Errors.**

| Mistake | What happens |
|---|---|
| anything after the name | `ERROR 20: SYNTAX ERROR` |

```c
// expect: error E_SYNTAX 3
#define A 1
#undef A B
int main(void) { return 0; }
```

**See also** `#define`, [The preprocessor](05_concepts.md#the-preprocessor).

---

## union

`union` -- **keyword** (not supported)

Reserved, and gives `ERROR 1: NOT SUPPORTED`. Leap-C has no unions.

```c
// expect: error E_NOTSUP 2
union u { int a; char b; };
```

**Notes.**

* To look at the same memory in two ways, use a pointer and a cast: `char *p = (char *)&n;` reads the bytes of an `int` `n`.

**See also** `struct`, `Casts`, [Differences from standard C](05_concepts.md#differences-from-standard-c).

---

## unsigned

`unsigned` -- **keyword**

A whole number of 16 bits, from 0 to 65535. `unsigned int` and `unsigned short` are the same. `unsigned char` is a byte from 0 to 255, the same as `char`. It wraps around at both ends: 0 - 1 is 65535.

```c
// expect: exit 0
// screen: 0 65535 0
// screen: 1 1
int main(void)
{
    unsigned u = 0;
    cls();
    u = u - 1;
    printf("%u %u\n", u, u + 1);
    printf("%d\n", u > 1);
    return 0;
}
```

`u > 1` is 1: the comparison is made on unsigned values, 65535 against 1.

**Notes.**

* **Unsigned wins.** When an `unsigned` and an `int` meet in an operator, both are treated as `unsigned`; this affects comparisons, `/`, `%` and `>>`.
* Print one with `%u`; `%d` shows values above 32767 as negative.
* A constant above 32767 is `unsigned`. A suffix `u` makes any constant `unsigned`.
* `unsigned long` is not supported.

**See also** `int`, `signed`, `char`, `Comparison operators`, [Numbers](05_concepts.md#numbers), [Conversions](05_concepts.md#conversions).

---

## VERIFY

`VERIFY "name"`, `VERIFY ""` -- **command**

Checks a tape against the program in the editor. Nothing is written and nothing in the program changes. `VERIFY "name"` looks for the program with that name; `VERIFY ""` takes the next program tape, whatever its name. The status row shows `VERIFYING`, then `VERIFYING name` when the header is found. Two rows are shown afterwards until a key is pressed:

| First row | When |
|---|---|
| `VERIFIED name` | the tape holds exactly the program in the editor, and ends where it does |
| `VERIFY FAILED` | the tape differs from the program |
| `BAD TAPE VERSION` | not a Leap-C tape |
| `BREAK` | SPACE or BREAK stopped it |
| `BAD NAME` | more than 10 characters, no closing quote, or something after it |

The second row is `SOURCE s B  FREE f B`.

```
VERIFY "hello"
```

**Notes.**

* Use it straight after `SAVE`, to be sure the tape is good.
* Like `LOAD`, it looks only at program tapes.

**See also** `SAVE`, `LOAD`, [Tapes](05_concepts.md#tapes).

---

## void

`void` -- **keyword**

Means "nothing". As a function's type, `void f(void)` is a function that returns no value; `(void)` in the parameter list says that it takes no arguments. A pointer to `void`, `void *`, can point at anything, and can be stored in, and taken from, any object pointer without a cast.

```c
// expect: exit 42
int x;
void set(int v)
{
    x = v;
}
int main(void)
{
    void *v;
    int *p;
    set(42);
    v = &x;
    p = v;
    return *p;
}
```

**Notes.**

* `main` may be `int main(void)` or `void main(void)`.
* You cannot declare a variable of type `void`, and cannot use the value of a `void` call: `x = set(1);` is an error.

**Errors.**

| Mistake | What happens |
|---|---|
| `void v;` | `ERROR 41: INCOMPLETE TYPE` |
| the value of a `void` call used (`f() + 1`) | `ERROR 51: BAD OPERAND TYPE` |
| a `void` parameter with a name, or `void` combined with another type word | `ERROR 25: BAD DECLARATOR` or `ERROR 24: BAD TYPE SPECIFIERS` |

**See also** `return`, `Pointer and address operators`, `Casts`, [Functions](05_concepts.md#functions), [Pointers](05_concepts.md#pointers).

---

## volatile

`volatile` -- **keyword** (not supported)

Reserved, and gives `ERROR 1: NOT SUPPORTED`. Leave it out.

```c
// expect: error E_NOTSUP 2
volatile int v;
```

**See also** `const`, [Differences from standard C](05_concepts.md#differences-from-standard-c).

---

## while

`while (` *expression* `)` *statement* -- **keyword**

Repeats the statement as long as the expression is not zero. The test is made **before** each time round, so the body may never run.

```c
// expect: exit 10
int main(void)
{
    int n = 1234, sum = 0;
    while (n > 0) {
        sum += n % 10;
        n /= 10;
    }
    return sum;
}
```

The loop adds the digits of 1234: 4, 3, 2, 1.

**Notes.**

* `while (1)` goes on until a `break`, a `return` or `exit`, or until BREAK is pressed.
* `break` leaves the loop; `continue` goes back to the test.

**Errors.**

| Mistake | What happens |
|---|---|
| a `void` call as the test | `ERROR 51: BAD OPERAND TYPE` |

```c
// expect: error E_OPERAND 5
void f(void) { }
int main(void)
{
    while (f()) ;
    return 0;
}
```

**See also** `do`, `for`, `break`, `continue`, `if`.
