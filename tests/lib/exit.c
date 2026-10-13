// exit(n) ends the program from any depth with status n, as main's return would.
// expect: exit 77
int depth(int n)
{
    if (n == 0) exit(77);
    return depth(n - 1) + 1;
}
int main(void)
{
    depth(20);
    return 1;
}
