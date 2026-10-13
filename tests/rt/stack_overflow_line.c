// A stack overflow (ENTER's check) is runtime error 1 at the line where the definition of the
// function being entered starts.
// expect: rterror 1
// rtline: 7
// noaudit
int helper(int x) { return x; }
int down(int n)
{
    return down(n + 1) + helper(n);
}
int main(void) { return down(0); }
