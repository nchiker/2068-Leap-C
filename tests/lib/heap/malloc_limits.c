// The heap is the source region above the source (spec.md 3.2): a request larger than the free
// space gives NULL, and so does any request of 32 KB or more; the heap can be used up and then,
// once freed, used again.
// expect: exit 0
int count;
char *a[200];
int main(void)
{
    int n;
    char *big;
    if (malloc(40000) != 0 || malloc(32767) != 0 || malloc(65535) != 0) return 1;
    n = 0;
    while (n < 200 && (a[n] = malloc(100)) != 0)
        n++;
    count = n;
    if (n < 100 || n >= 200) return 2;
    if (malloc(100) != 0) return 3;
    while (n > 0)
        free(a[--n]);
    big = malloc(count * 100);
    if (big == 0) return 4;
    free(big);
    if (malloc(count * 102 + 200) != 0) return 5;
    return 0;
}
