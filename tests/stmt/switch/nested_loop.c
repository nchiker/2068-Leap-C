// switch inside a loop: break leaves the switch, continue the loop iteration; a nested switch.
// expect: exit 0
int main(void)
{
    int i;
    int n;
    int m;
    n = 0;
    m = 0;
    for (i = 0; i < 6; i++) {
        switch (i % 3) {
        case 0:
            n += 1;
            break;
        case 1:
            switch (i) {
            case 1: m += 10; break;
            case 4: m += 40; continue;
            }
            n += 100;
            break;
        default:
            continue;
        }
        n += 1000;
    }
    if (n != 2 * 1001 + 1100) return 1;
    if (m != 50) return 2;
    return 0;
}
