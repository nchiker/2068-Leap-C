// A negative sprite width is runtime error 4 (not a huge rectangle).
// expect: rterror 4
char buf[90];
int main(void)
{
    sprite_put(0, 0, -1, 1, buf);
    return 0;
}
