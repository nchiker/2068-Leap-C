// inkey() returns the key pressed since the last read, or 0 at once if there is none.
// expect: exit 0
// keys: NONE "x" NONE NONE "7"
int main(void)
{
    if (inkey() != 0) return 1;
    if (inkey() != 'x') return 2;
    if (inkey() != 0) return 3;
    if (inkey() != 0) return 4;
    if (inkey() != '7') return 5;
    return 0;
}
