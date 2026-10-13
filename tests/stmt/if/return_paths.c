// Every path of a function returns, with code after `if`s that return.
// expect: exit 321
int sign(int x)
{
    if (x < 0)
        return 1;
    if (x == 0)
        return 2;
    return 3;
}
int main(void) { return sign(5) * 100 + sign(0) * 10 + sign(-9); }
