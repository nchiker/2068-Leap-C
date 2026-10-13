// The library's prototypes are known without a header: a call with the wrong number of arguments
// is a compile error.
// expect: error E_ARGS 7
int main(void)
{
    plot(1, 2);
    plot(1);
    return 0;
}
