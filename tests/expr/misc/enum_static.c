// Enum constants in expressions, static locals, initialised globals read and written by code.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
enum { A = 3, B, C = A * 10 };
int g = 7;
char msg[] = "xyz";
int count(void) { static int k = 100; return ++k; }
int main(void)
{
    ck(1, B + C, 34);
    ck(2, g * A, 21);
    g = C;
    ck(3, g, 30);
    ck(4, msg[2], 'z');
    count();
    ck(5, count(), 102);
    return bad;
}
