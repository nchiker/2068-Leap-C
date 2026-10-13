// A continue that reaches the end of a function through do ... while (0) right after a return:
// the function's final LEAVE must still be there (else the code runs on into h, which sets g).
// expect: exit 0
int g;
void f(int x)
{
    do {
        if (x) continue;
        return;
    } while (0);
}
void h(void) { g = 7; }
int main(void) { f(1); f(0); return g; }
