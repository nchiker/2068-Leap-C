// A macro expanding to more than 255 tokens: NESTING TOO DEEP (spec.md 4.8; Phase 9: ROM coverage).
// expect: error E_NESTING 9
#define A x + x + x + x + x + x + x + x + x + x
#define B A + A + A + A + A
#define C B + B + B + B
int main(void)
{
    int x = 1;
    return C;
}
