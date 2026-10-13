// Object-like macros: constants, expressions, array sizes, macros of macros, an empty macro.
// expect: exit 0
#define N 10
#define M (N * 2)
#define EMPTY
#define ADD +
#define TWO 1 ADD 1
int a[N];
int b[M];
int main(void)
{
    EMPTY
    int i;
    for (i = 0; i < N; i++) a[i] = i;
    if (sizeof(b) != 40) return 1;
    if (TWO != 2) return 2;
    if (a[N - 1] != 9) return 3;
    EMPTY;
    return M - 20;
}
