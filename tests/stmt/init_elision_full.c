// Brace elision that fills an inner aggregate exactly, then goes on with the outer one (C89 6.5.7)
// (Phase 9: ROM coverage).
// expect: exit 123
struct s { int a[2]; int b; } v = { 1, 2, 3 };
int main(void)
{
    return v.a[0] * 100 + v.a[1] * 10 + v.b;
}
