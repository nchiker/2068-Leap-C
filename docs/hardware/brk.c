/* Leap-C hardware check H8: BREAK (CAPS SHIFT + SPACE) stops this loop: "BREAK", "LINE 2". */
int main(void)
{
    unsigned n = 0;
    for (;;) {
        at(0, 0);
        printf("%u", n++);
    }
}
