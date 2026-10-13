// An empty sprite rectangle is runtime error 4.
// expect: rterror 4
// rtline: 4
int main(void)
{
    char b[9];
    sprite_get(0, 0, 0, 1, b);
    return 0;
}
