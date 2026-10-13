// ++ of a void * (pointer arithmetic needs a complete element type).
// expect: error E_INCOMPLETE 7
int main(void)
{
    void *p;
    p = 0;
    p++; /*E*/
    return 0;
}
