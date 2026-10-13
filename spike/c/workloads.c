/* The C source the spike's hand-assembled workloads stand for (conventional formatting).
   Used only to measure code bytes per source byte; nothing compiles this file. */
int sum(int n)
{
    int s;
    s = 0;
    while (n) {
        s += n;
        --n;
    }
    return s;
}

void copy(char *d, char *s, unsigned n)
{
    while (n--)
        *d++ = *s++;
}

int a[100];

int asum(int n)
{
    int i;
    int t;
    t = 0;
    for (i = 0; i < n; i++)
        t += a[i];
    return t;
}

struct pt {
    int x;
    int y;
    char c;
};
struct pt pts[20];

void move(struct pt *p, int n, int dx)
{
    while (n--) {
        p->x += dx;
        p->y += p->x;
        p++;
    }
}

int fact(int n)
{
    int r;
    if (n <= 1)
        return 1;
    r = n * fact(n - 1);
    return r;
}
