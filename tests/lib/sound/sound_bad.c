// An AY register beyond 15 is runtime error 4.
// expect: rterror 4
// rtline: 4
int main(void)
{
    sound(0, 1);
    sound(16, 0);
    return 0;
}
