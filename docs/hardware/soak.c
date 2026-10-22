/* Leap-C hardware check H10: a soak. Rounds of integer, float, heap, string and screen work, each
   checked; runs until a key is pressed, then reports the rounds and any failure. Leave it an hour. */
char text[64];
int main(void)
{
    unsigned round = 0, f0 = frames();
    int fail = 0, i;
    char *p;
    float x;
    cls();
    while (!inkey() && !fail) {
        unsigned s = 0;
        for (i = 0; i < 200; i++)
            s += i * i;
        if (s != 25260u)              /* 2,646,700 modulo 65,536 */
            fail = 1;
        x = round % 100;
        if ((int)(x * 0.5 * 2) != (int)(round % 100))
            fail = 2;
        p = malloc(300 + round % 200);
        if (!p)
            fail = 3;
        else {
            memset(p, round, 300);
            if (p[299] != (char)round)
                fail = 4;
            free(p);
        }
        strcpy(text, "LEAP-C SOAK ");
        itoa(round, text + strlen(text), 10);
        if (strlen(text) < 13)
            fail = 5;
        at(0, 0);
        puts(text);
        printf("%u FRAMES", frames() - f0);
        round++;
    }
    at(2, 0);
    printf("%u ROUNDS, %s %d", round, fail ? "SOAK FAIL" : "SOAK PASS", fail);
    return fail;
}
