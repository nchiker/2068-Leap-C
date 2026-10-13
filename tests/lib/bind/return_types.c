// Return types: malloc's void * converts to any object pointer; strchr gives a char *;
// strlen and frames are unsigned (comparisons above 32767 are unsigned).
// expect: exit 0
int *ip;
int main(void)
{
    char *s;
    ip = malloc(4);
    s = malloc(10);
    strcpy(s, "abc");
    *strchr(s, 'b') = 'X';
    if (s[1] != 'X') return 1;
    if (strlen(s) - 4 < 0) return 2;
    if (strchr(s, 'c') - s != 2) return 3;
    *ip = 7;
    return *ip - 7;
}
