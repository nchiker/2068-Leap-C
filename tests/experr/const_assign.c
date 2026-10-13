// Assignment to a const object.
// expect: error E_CONST 6
const int c = 1;
int main(void)
{
    c = 2; /*E*/
    return 0;
}
