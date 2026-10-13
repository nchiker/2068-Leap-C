// && and || as conditions, with short-circuit side effects.
// expect: exit 0
int n;
int bump(int v) { n++; return v; }
int main(void)
{
    if (bump(0) && bump(1)) return 1;
    if (n != 1) return 2;
    if (!(bump(1) || bump(1))) return 3;
    if (n != 2) return 4;
    if (bump(1) && bump(0) || bump(1)) n += 10; else return 5;
    if (n != 15) return 6;
    return 0;
}
