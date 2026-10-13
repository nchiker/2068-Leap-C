// Arithmetic on a pointer to an incomplete struct.
// expect: error E_INCOMPLETE 8
struct later;
int main(void)
{
    struct later *p;
    p = 0;
    p = p + 1; /*E*/
    return 0;
}
