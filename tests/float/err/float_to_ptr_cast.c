// A pointer does not cast to a float.
// expect: error E_OPERAND 7
int x;
int main(void)
{
    float f;
    f = (float)&x;
    return 0;
}
