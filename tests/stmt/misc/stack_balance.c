// Loops with calls and held operands keep the stack balanced over many iterations.
// expect: exit 0
int id(int x) { return x; }
int main(void)
{
    int i;
    int s;
    s = 0;
    for (i = 0; i < 300; i++) {
        s += id(i) - id(i) + (id(1) ? id(1) : id(2));
        while (id(0)) ;
        switch (id(i) & 1) { case 0: s += 0; break; case 1: s += id(0); }
    }
    return s - 300;
}
