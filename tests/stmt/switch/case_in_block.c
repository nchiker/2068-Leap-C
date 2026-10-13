// Case labels inside a nested block of the switch body (Duff's device shape).
// expect: exit 0
char from[20];
char to[20];
void dcopy(char *d, char *s, int count)
{
    int n;
    n = (count + 3) / 4;
    switch (count % 4) {
    case 0: do { *d++ = *s++;
    case 3:      *d++ = *s++;
    case 2:      *d++ = *s++;
    case 1:      *d++ = *s++;
            } while (--n > 0);
    }
}
int main(void)
{
    int i;
    for (i = 0; i < 20; i++) from[i] = i + 1;
    dcopy(to, from, 15);
    for (i = 0; i < 15; i++) if (to[i] != i + 1) return 1;
    if (to[15] != 0) return 2;
    return 0;
}
