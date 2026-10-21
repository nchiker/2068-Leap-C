// tape_save() needs a name of 1-10 characters: an empty one is runtime error 4 at the call's function,
// before anything is sent (no tape needed).
// expect: rterror 4
// rtline: 6
char buf[8];
int main(void)
{
    tape_save("", buf, 8);
    return 0;
}
