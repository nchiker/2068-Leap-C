// The four workloads of the code-shape spike (spike/c/workloads.c), compiled by the real compiler:
// tools/stmtbench.py compares their code size and T-states with the spike's mixed-template output
// (docs/C_FEASIBILITY_STUDY.md 4). main only sets up the data.
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

char src[256];
char dst[256];

int main(void)
{
    int i;
    for (i = 0; i < 100; i++) a[i] = i;
    for (i = 0; i < 256; i++) src[i] = i;
    for (i = 0; i < 20; i++) { pts[i].x = i; pts[i].y = 0; pts[i].c = 0; }
    return 0;
}
