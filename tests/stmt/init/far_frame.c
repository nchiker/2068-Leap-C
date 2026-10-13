// Initialised locals beyond (ix+d)'s reach (a 190-byte frame).
// expect: exit 0
int main(void)
{
    char big[180];
    int far1 = 1234;
    int far2 = far1 + 1;
    big[0] = 1;
    big[179] = 2;
    if (far1 != 1234 || far2 != 1235) return 1;
    if (big[0] + big[179] != 3) return 2;
    return 0;
}
