// An expression statement without `;`.
// expect: error E_SYNTAX 7
int x;
int main(void)
{
    x = 1
    return x; /*E*/
}
