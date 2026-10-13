// A switch without case labels, with only a default, with a default in the middle.
// expect: exit 0
int main(void)
{
    int r;
    r = 1;
    switch (r) { r = 5; }
    if (r != 1) return 1;
    switch (r) { default: r = 2; }
    if (r != 2) return 2;
    switch (r) { case 1: r = 10; break; default: r = 20; case 3: r++; }
    if (r != 21) return 3;
    switch (3) { case 1: r = 10; break; default: r = 20; case 3: r++; }
    if (r != 22) return 4;
    return 0;
}
