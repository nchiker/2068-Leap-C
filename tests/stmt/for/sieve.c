// A sieve of Eratosthenes: the primes below 1000.
// expect: exit 168
char flags[1000];
int main(void)
{
    int i;
    int k;
    int count;
    count = 0;
    for (i = 2; i < 1000; i++) flags[i] = 1;
    for (i = 2; i < 1000; i++) {
        if (!flags[i]) continue;
        count++;
        for (k = i + i; k < 1000; k += i) flags[k] = 0;
    }
    return count;
}
