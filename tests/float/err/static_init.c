// A static float's initialiser must be constant.
// expect: error E_CONSTEXPR 4
float g = 1.0;
float h = g * 2;
int main(void)
{
    return 0;
}
