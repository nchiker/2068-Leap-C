// << >> take integers only.
// expect: error E_OPERAND 6
float f = 1.0;
int main(void)
{
    return 1 << f;
}
