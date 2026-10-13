// Macros in call arguments (the compiler rescans arguments: the expansion must be made again).
// expect: exit 0
#define A 7
#define B (A + 1)
#define CALL add3(A, B, A * B)
int add3(int x, int y, int z) { return x * 100 + y * 10 + z; }
int sub(int x, int y) { return x - y; }
int main(void)
{
    if (add3(A, B, 3) != 783) return 1;
    if (sub(B, A) != 1) return 2;
    if (sub(sub(B, A), sub(A, B)) != 2) return 3;
    if (CALL != 700 + 80 + 56) return 4;
    if (add3((A), (B), (A)) != 787) return 5;
    return 0;
}
