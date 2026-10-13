// strlen, strcpy, strcat, strncpy, strcmp, strchr at their boundaries: empty strings, n = 0,
// padding with NULs, characters above 127 compared unsigned, the NUL as a searched character.
// expect: exit 0
char a[16];
char b[16];
int main(void)
{
    char *p;
    if (strlen("") != 0 || strlen("abc") != 3) return 1;
    if (strcpy(a, "hello") != a || strcmp(a, "hello") != 0) return 2;
    if (strcat(a, ", C") != a || strcmp(a, "hello, C") != 0 || strlen(a) != 8) return 3;
    strcpy(a, "");
    strcat(a, "");
    if (a[0] != 0) return 4;
    memset(b, 'x', 16);
    if (strncpy(b, "ab", 5) != b) return 5;
    if (b[0] != 'a' || b[1] != 'b' || b[2] != 0 || b[3] != 0 || b[4] != 0 || b[5] != 'x') return 6;
    strncpy(b, "longer", 3);
    if (b[0] != 'l' || b[2] != 'n' || b[3] != 0) return 7;
    strncpy(b, "zz", 0);
    if (b[0] != 'l') return 8;
    if (strcmp("abc", "abd") >= 0 || strcmp("abd", "abc") <= 0) return 9;
    if (strcmp("ab", "abc") >= 0 || strcmp("abc", "ab") <= 0 || strcmp("", "") != 0) return 10;
    if (strcmp("\x80", "\x7f") <= 0) return 11;
    p = strchr("hello", 'l');
    if (p == 0 || *p != 'l' || p[1] != 'l') return 12;
    if (strchr("hello", 'z') != 0) return 13;
    p = strchr("hello", 0);
    if (p == 0 || *p != 0) return 14;
    if (strchr("hello", 'h' + 256) == 0) return 15;
    return 0;
}
