// BREAK deep in a recursion (a loop at the bottom) unwinds every frame at once.
// expect: rterror 5
// rtline: 9
// break: after 400000
// breakpc: 0xC000 0xE000
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
int rec(int n)
{
    if (n == 0)
        for (;;) n--;
    return rec(n - 1) + 1;
}
int main(void)
{
    return rec(200);
}
