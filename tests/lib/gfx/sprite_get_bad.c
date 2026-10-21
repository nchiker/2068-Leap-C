// sprite_get with a rectangle not wholly on the screen is runtime error 4, as sprite_put is.
// expect: rterror 4
char buf[90];
int main(void)
{
    sprite_get(23, 0, 1, 2, buf);
    return 0;
}
