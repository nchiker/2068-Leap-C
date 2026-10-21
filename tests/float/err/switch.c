// switch takes an integer (spec.md 4.5).
// expect: error E_OPERAND 6
float f = 1.0;
int main(void)
{
    switch (f) {
    }
    return 0;
}
