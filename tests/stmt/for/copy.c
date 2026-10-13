// The spike's `copy` (a byte copy loop).
// expect: exit 0
char src[256];
char dst[256];
void copy(char *d, char *s, unsigned n) { while (n--) *d++ = *s++; }
int main(void)
{
    int i;
    for (i = 0; i < 256; i++) src[i] = i;
    copy(dst, src, 256);
    for (i = 0; i < 256; i++)
        if (dst[i] != i) return 1;
    return 0;
}
