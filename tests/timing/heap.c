// Timing fixture (Phase 9): the heap: 150 rounds of allocations of several sizes, filled and freed.
int main(void)
{
    char *p[6];
    int r, k, n = 0;
    for (r = 0; r < 150; r++) {
        for (k = 0; k < 6; k++) {
            p[k] = malloc(40 + k * 30 + r % 7);
            if (p[k]) {
                memset(p[k], r, 40);
                n++;
            }
        }
        for (k = 5; k >= 0; k--)
            free(p[k]);
    }
    return n;
}
