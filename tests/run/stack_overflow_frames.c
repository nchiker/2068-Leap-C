// Recursion with 100-byte frames overflows after about 15 levels: runtime error 1.
// expect: rterror 1
// noaudit
int deep(int n)
{
    char buf[100];
    buf[0] = n;
    return deep(n + 1) + buf[0];
}
int main(void) { return deep(1); }
