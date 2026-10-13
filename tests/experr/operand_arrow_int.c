// -> on an int.
// expect: error E_OPERAND 6
int x;
int main(void)
{
    return x->y; /*E*/
}
