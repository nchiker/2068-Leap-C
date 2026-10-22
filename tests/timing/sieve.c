// Timing fixture (Phase 9): the sieve of Eratosthenes over 8,000 flags (a global array in region 1).
char flag[8000];
int main(void)
{
    int i, k, n = 0;
    for (i = 2; i < 8000; i++)
        if (!flag[i]) {
            n++;
            for (k = i + i; k < 8000; k += i)
                flag[k] = 1;
        }
    return n;
}
