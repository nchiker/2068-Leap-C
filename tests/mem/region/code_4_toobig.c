// Code that overflows image region 4, the last region: PROGRAM TOO BIG at the statement whose
// code no longer fits (regions 1-3 full of data; region 4 keeps 144 bytes, of which g and main's
// function -> line record take 8: 17 statements fit).
// expect: error E_TOOBIG 29
char a[8192];
char b[4480];
char c[1024];
char d[6000];
int g;
int main(void)
{
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    g = g + 1;
    return g;
}
