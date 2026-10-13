// Recursion with locals and parameters: each level keeps its own frame.
// expect: exit 5050
int sum(int n)
{
    int here;
    int rest;
    here = n;
    rest = n > 0 ? sum(n - 1) : 0;
    return here + rest;
}
int main(void) { return sum(100); }
// noaudit
