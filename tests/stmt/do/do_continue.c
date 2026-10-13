// continue in a do loop goes to the condition; break leaves the loop.
// expect: exit 0
int main(void)
{
    int i;
    int s;
    i = 0;
    s = 0;
    do {
        i++;
        if (i == 3) continue;
        if (i == 7) break;
        s += i;
    } while (i < 100);
    if (i != 7) return 1;
    if (s != 1 + 2 + 4 + 5 + 6) return 2;
    i = 0;
    do {
        i++;
        if (i < 5) continue;
    } while (i < 5);
    return i - 5;
}
