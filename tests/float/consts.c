// Float constant expressions (Phase 8; spec.md 4.4, 4.7): folded at compile time, so they size arrays
// through casts, initialise static data of float and integer objects, and give case labels.
// expect: exit 0
// mem: f+0 834800000082c000000082400000008260000000
// mem: k+0 0700410003000a00
// mem: n+0 0300
float f[4] = { 1.0 / 4 + 2 * 3, -(1.5 * 2), 3, (float)7 / 2 };
int k[4] = { 7.9, 'A' + 0.5, (int)3.99, 10.0 };
int a[(int)3.7];
int n = sizeof(a) / sizeof(int) * (sizeof(float) == 5) * (sizeof 1.5 == 5) * (sizeof(double) == 5);
enum { TWO = (int)2.0 };
int main(void)
{
    switch (k[2]) {
    case TWO:
        return 1;
    case (int)3.5:
        return 0;
    }
    return 2;
}
