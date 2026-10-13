// expect: error E_OPERAND 5
void f(void) { }
int main(void)
{
    while (f()) ;
    return 0;
}
