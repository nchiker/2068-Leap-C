// Without a library, image region 3 is open to the program (the twin of region3.c): the same object goes to
// region 3 (Phase 10).
// region: c 3
// expect: exit 7
char a[8000];
char b[4400];
char c[900];
int main(void)
{
    c[899] = 1;
    return 7;
}
