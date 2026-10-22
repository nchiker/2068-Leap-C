// && and || folded in constant expressions (enumerators, array sizes), and an unsigned % folded
// (Phase 9: ROM coverage).
// expect: exit 0
enum { T = 5 && 0, U = 0 || 9, V = 3 && 4, W = 0 || 0, M = 40000u % 7 };
char a[(1 && 2) + (0 || 7)];
int main(void)
{
    if (T != 0 || U != 1 || V != 1 || W != 0)
        return 1;
    if (sizeof a != 2 || M != 2)
        return 2;
    return 0;
}
