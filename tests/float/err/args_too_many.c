// Eleven float arguments are 33 pending words with the format's: more than the 32 a call may hold
// (spec.md 4.10): NESTING TOO DEEP (Phase 9: ROM coverage, a float argument's slot).
// expect: error E_NESTING 6
int main(void)
{
    printf("%f", 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0);
    return 0;
}
