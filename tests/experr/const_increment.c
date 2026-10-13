// ++ of a const local.
// expect: error E_CONST 6
int main(void)
{
    const int k;
    k++; /*E*/
    return 0;
}
