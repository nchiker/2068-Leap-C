// Function pointers as parameters, struct members and locals; calls with argument expressions.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
struct op { int (*fn)(int); int arg; };
int neg(int x) { return -x; }
int twice(int x) { return 2 * x; }
int apply(int (*f)(int), int v) { return f(v); }
int compose(int (*f)(int), int (*g)(int), int v) { return f(g(v)); }
struct op o;
int main(void)
{
    int (*l)(int);
    l = twice;
    ck(1, apply(neg, 5), -5);
    ck(2, apply(l, 5), 10);
    ck(3, compose(neg, twice, 3), -6);
    o.fn = neg;
    o.arg = 9;
    ck(4, o.fn(o.arg), -9);
    ck(5, (&o)->fn(apply(twice, 1)), -2);
    return bad;
}
