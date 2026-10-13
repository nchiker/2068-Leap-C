// rand() and srand() through the compiler's binding: rand() is 0..RAND_MAX (32767), every run
// starts with the sequence of srand(1), and srand(n) restarts a sequence.
// expect: exit 0
int first[4];
int main(void)
{
    int i;
    int r;
    for (i = 0; i < 4; i++) first[i] = rand();
    srand(1);
    for (i = 0; i < 4; i++)
        if (rand() != first[i]) return 1;
    srand(0);
    if (rand() != first[0]) return 2;
    srand(12345);
    r = rand();
    srand(12345);
    if (rand() != r) return 3;
    for (i = 0; i < 1000; i++)
        if (rand() < 0) return 4;
    return 0;
}
