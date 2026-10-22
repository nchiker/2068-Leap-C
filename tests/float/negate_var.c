// Unary minus of a float object, not a constant: the float core's negation at run time (Phase 9: ROM
// coverage found only constants negated).
// expect: exit -10
float g = 1.25;
int main(void)
{
    float x = 2.5, y;
    y = -x;
    if (-y != x || -g + 1.25 != 0)
        return 1;
    return y * 4;
}
