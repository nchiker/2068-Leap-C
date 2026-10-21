// beep: a semitone below -60 is runtime error 4.
// expect: rterror 4
int main(void)
{
    beep(1, -61);
    return 0;
}
