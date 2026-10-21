// ~ takes an integer only.
// expect: error E_OPERAND 6
float f = 1.0;
int main(void)
{
    f = ~f;
    return 0;
}
