// An element of a const array is const.
// expect: error E_CONST 6
const int t[3] = { 1, 2, 3 };
int main(void)
{
    t[1] = 5; /*E*/
    return 0;
}
