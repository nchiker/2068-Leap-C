// A frame that does not fit above the floor is never made: ENTER checks the new stack pointer
// before it moves SP (src/runtime/helpers.asm), so recursion with 250 bytes of locals ends with a
// stack overflow at the floor and nothing below $F800 (image region 3) is written.
// expect: rterror 1
// rtline: 8
// stacklow: $F800
// noaudit
int f(int n)
{
    char big[250];
    big[0] = n;
    big[249] = n;
    return f(n + 1) + big[0];
}
int main(void)
{
    return f(1);
}
