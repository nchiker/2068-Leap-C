// return in a void function, from loops and switches.
// expect: exit 0
int g;
void set(int v)
{
    int i;
    for (i = 0; ; i++) {
        if (i == v) { g = i; return; }
    }
}
void sw(int v)
{
    switch (v) {
    case 1: g = 10; return;
    default: g = 20;
    }
}
int main(void)
{
    set(7);
    if (g != 7) return 1;
    sw(1);
    if (g != 10) return 2;
    sw(2);
    if (g != 20) return 3;
    return 0;
}
