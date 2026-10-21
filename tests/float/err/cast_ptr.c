// A float does not cast to a pointer, nor a pointer to a float.
// expect: error E_OPERAND 5
int main(void)
{
    return *(int *)1.5;
}
