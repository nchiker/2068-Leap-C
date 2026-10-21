// An empty sprite rectangle (height 0) is runtime error 4.
// expect: rterror 4
char buf[90];
int main(void)
{
    sprite_get(0, 0, 1, 0, buf);
    return 0;
}
