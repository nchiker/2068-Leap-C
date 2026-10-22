// Timing fixture (Phase 9): text output, 8 screens of 22 rows (display file writes: contended memory).
int main(void)
{
    int k, n;
    for (k = 0; k < 8; k++) {
        at(0, 0);
        for (n = 0; n < 32 * 22; n++)
            putchar('A' + (n + k) % 26);
    }
    return k;
}
