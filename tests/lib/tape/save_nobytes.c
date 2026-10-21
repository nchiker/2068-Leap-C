// tape_save() of no bytes: runtime error 4 (a block of no bytes cannot be loaded back).
// expect: rterror 4
// rtline: 5
char buf[8];
int main(void)
{
    tape_save("empty", buf, 0);
    return 0;
}
