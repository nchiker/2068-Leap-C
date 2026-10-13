// A library error in main is reported at main's line; the program's later code does not run.
// expect: rterror 4
// rtline: 5
int g;
int main(void)
{
    g = 1;
    mode(7);
    g = 2;
    return 0;
}
