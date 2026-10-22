// A floating constant whose exponent has more digits than the float core keeps (XF_ATOF clamps it at
// 999): far below the smallest float, it is 0 (Phase 9: ROM coverage).
// expect: exit 1
int main(void)
{
    float f = 1e-12345;
    return f == 0;
}
