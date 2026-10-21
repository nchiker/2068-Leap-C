// Nor a pointer to a float.
// expect: error E_TYPE 7
int x;
int main(void)
{
    float f;
    f = &x;
    return 0;
}
