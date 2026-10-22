// A floating constant whose exponent has more digits than the float core keeps (clamped at 999): far
// beyond the largest float, NUMBER TOO LARGE (Phase 9: ROM coverage).
// expect: error E_RANGE 7
int main(void)
{
    float f;
    f = 1e12345;
    return 0;
}
