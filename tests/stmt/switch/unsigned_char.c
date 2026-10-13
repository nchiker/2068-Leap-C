// switch on char (promoted) and on unsigned values above 32767.
// expect: exit 0
int c(char ch)
{
    switch (ch) {
    case 'a': return 1;
    case 'b': return 2;
    case 255: return 3;
    default: return 0;
    }
}
int u(unsigned x)
{
    switch (x) {
    case 65535u: return 1;
    case 32768u: return 2;
    case 0: return 3;
    case 1: return 4;
    }
    return 5;
}
int main(void)
{
    if (c('a') != 1 || c('b') != 2 || c(255) != 3 || c('c') != 0) return 1;
    if (u(65535u) != 1 || u(32768u) != 2 || u(0) != 3 || u(1) != 4 || u(2) != 5 || u(32767) != 5) return 2;
    return 0;
}
