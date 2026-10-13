// sprite_get() copies w x h cells (9 bytes each: 8 pixel rows, the attribute) from the screen;
// sprite_put() puts them back anywhere.
// expect: exit 0
// screen: 10 AB
// screen: 11 CD
// screen: 20                               AB
// screen: 21                               CD
// attr: 20 30 0x0A
char buf[36];
int main(void)
{
    cls();
    ink(2);
    paper(1);
    print("AB\nCD");
    sprite_get(0, 0, 2, 2, buf);
    if (buf[8] != 0x0A || buf[35] != 0x0A) return 1;
    cls();
    sprite_put(10, 0, 2, 2, buf);
    sprite_put(20, 30, 2, 2, buf);
    return 0;
}
