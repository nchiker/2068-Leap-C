// A letter after a floating constant (other than the f, F, l, L suffixes): BAD NUMBER.
// expect: error E_NUMBER 5
int main(void)
{
    return 2.5q;
}
