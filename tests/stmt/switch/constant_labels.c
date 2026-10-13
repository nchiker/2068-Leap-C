// Case labels from enumeration constants, character constants and constant expressions.
// expect: exit 0
enum color { RED, GREEN = 5, BLUE };
int f(int c)
{
    switch (c) {
    case RED: return 1;
    case GREEN: return 2;
    case BLUE: return 3;
    case 'A' + 1: return 4;
    case 2 * 50 + sizeof(int): return 5;
    case -GREEN: return 6;
    }
    return 0;
}
int main(void)
{
    if (f(0) != 1 || f(5) != 2 || f(6) != 3 || f(66) != 4 || f(102) != 5 || f(-5) != 6 || f(7) != 0) return 1;
    return 0;
}
