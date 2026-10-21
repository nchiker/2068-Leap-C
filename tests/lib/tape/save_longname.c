// tape_save() with a name of 11 characters: runtime error 4 (the header's field holds 10).
// expect: rterror 4
// rtline: 5
char buf[8];
int main(void)
{
    tape_save("abcdefghijk", buf, 8);
    return 0;
}
