// Division of a float by zero at run time: runtime error 6 (Spectrum BASIC's "Number too big"; Phase 8).
// expect: rterror 6
// rtline: 5
float zero;
int main(void)
{
    float q;
    q = 1.0;
    q = q / zero;
    return 1;
}
