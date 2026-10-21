// A float operation's overflow ends the program with runtime error 6 (NUMBER TOO BIG; Phase 8), at the
// line of the function whose code failed.
// expect: rterror 6
// rtline: 6
float big = 1e30;
float square(float x)
{
    return x * x;
}
int main(void)
{
    square(1e10);
    square(big);
    return 0;
}
