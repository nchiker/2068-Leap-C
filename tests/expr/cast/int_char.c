// Casts between the integer types: truncation, zero and sign extension, and back.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int main(void)
{
    int i;
    unsigned u;
    char c;
    signed char s;
    i = 0x1234;
    ck(1, (char)i, 0x34);
    ck(2, (signed char)0xF0, -16);
    i = 0x80;
    ck(3, (signed char)i, -128);
    ck(4, (char)(signed char)i, 128);
    s = -2;
    ck(5, (unsigned)s, 65534);
    ck(6, (char)s, 254);
    u = 65535;
    ck(7, (int)u, -1);
    c = 255;
    ck(8, (signed char)c, -1);
    ck(9, (int)(char)(i + 0x100), 0x80);
    return bad;
}
