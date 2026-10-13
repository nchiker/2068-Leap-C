// A name that is not the library's stays an undeclared function: E_UNDEFFN at its first use.
// expect: error E_UNDEFFN 5
int main(void)
{
    prnt("x");
    return 0;
}
