// A sprite rectangle not wholly on the screen (or empty) is runtime error 4, reported at the line
// where the calling function's definition starts.
// expect: rterror 4
// rtline: 7
char buf[90];

void show(void)
{
    sprite_put(22, 31, 1, 3, buf);
}
int main(void)
{
    sprite_get(0, 0, 1, 1, buf);
    show();
    return 0;
}
