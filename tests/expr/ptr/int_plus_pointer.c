// An integer plus a pointer, the integer first: a constant, a variable, a computed value (C89 6.3.6)
// (Phase 9: ROM coverage found `i + p` never compiled).
// expect: exit 0
int v[6] = {10, 11, 12, 13, 14, 15};
int main(void)
{
    int i = 2, *p = v;
    if (*(3 + p) != 13)
        return 1;
    if (*(i + p) != 12)
        return 2;
    if (*(i * 2 + v) != 14)
        return 3;
    if (*(1 + (p + 1)) != 12)
        return 4;
    if (*(i + (p + 1)) != 13)
        return 5;
    if (*((i * 2) + (p + 1)) != 15)
        return 6;
    return 0;
}
