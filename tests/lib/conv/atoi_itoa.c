// atoi: leading spaces and control characters, a sign, digits up to the first non-digit, 16-bit
// wraparound. itoa: bases 2-36 (lowercase), negative only in base 10, -32768; it returns buf.
// expect: exit 0
char s[20];
int main(void)
{
    if (atoi("0") != 0 || atoi("12345") != 12345 || atoi("-32768") != -32768) return 1;
    if (atoi("  \t+42abc") != 42 || atoi("\n-7") != -7 || atoi("") != 0 || atoi("x1") != 0) return 2;
    if (atoi("65535") != -1 || atoi("70000") != 4464 || atoi("- 5") != 0) return 3;
    if (itoa(0, s, 10) != s || strcmp(s, "0")) return 4;
    itoa(-32768, s, 10);
    if (strcmp(s, "-32768")) return 5;
    itoa(-1, s, 16);
    if (strcmp(s, "ffff")) return 6;
    itoa(255, s, 2);
    if (strcmp(s, "11111111")) return 7;
    itoa(35, s, 36);
    if (strcmp(s, "z")) return 8;
    itoa(-1, s, 2);
    if (strcmp(s, "1111111111111111")) return 9;
    itoa(511, s, 8);
    if (strcmp(s, "777")) return 10;
    itoa(12345, s, 10);
    if (atoi(s) != 12345) return 11;
    return 0;
}
