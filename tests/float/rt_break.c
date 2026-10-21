// BREAK during a float operation (the EXROM's float core: a NOBRK section, spec.md 5.8) waits for its
// end, then the program ends with runtime error 5 at the line of the function that called it.
// expect: rterror 5
// rtline: 8
// break: at FDIV
// breakdeferred
// noaudit
float slow(float x)
{
    while (1)
        x = x / 1.0001;
    return x;
}
int main(void)
{
    slow(123.0);
    return 0;
}
