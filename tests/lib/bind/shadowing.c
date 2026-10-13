// The library's names are not reserved: a program's own declaration comes first, at file scope
// (a function, a variable) and in a block.
// expect: exit 0
int print(int x) { return x + 1; }
int frames = 5;
int main(void)
{
    int abs;
    abs = -3;
    if (print(1) != 2) return 1;
    if (frames != 5) return 2;
    if (abs != -3) return 3;
    {
        int (*p)(int) = putchar;
        if (p == 0) return 4;
    }
    return 0;
}
