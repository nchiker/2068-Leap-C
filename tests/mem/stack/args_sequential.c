// Calls one after another do not accumulate: each pops its arguments (32 words each). A call
// inside an argument counts the words its enclosing call has pushed: 1 + 31.
// expect: exit 46
int f();
int main(void)
{
    int s;
    s = f(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
          1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1);
    s = s + f(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1);
    s = s + f(f(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1), 0);
    return s + f(f(1, 2), f(3, 4), f(5, 6)) + 30;
}
int f(int a, int b) { return a + b; }
