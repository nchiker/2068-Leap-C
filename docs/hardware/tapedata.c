/* Leap-C hardware check H9: a data tape. Saves 2,000 bytes, then loads them back and compares:
   record, then rewind and play when asked (ENTER, not SPACE: SPACE is BREAK during a transfer). */
char buf[2000];
int main(void)
{
    int i, n, bad = 0;
    for (i = 0; i < 2000; i++)
        buf[i] = i * 7 + 3;
    puts("RECORD, THEN PRESS ENTER");
    getkey();
    tape_save("leapdata", buf, 2000);
    memset(buf, 0, 2000);
    puts("REWIND, PLAY, PRESS ENTER");
    getkey();
    n = tape_load("leapdata", buf, 2000);
    for (i = 0; i < 2000; i++)
        if (buf[i] != (char)(i * 7 + 3))
            bad++;
    printf("LOADED %d BYTES, %d WRONG\n%s", n, bad, n == 2000 && !bad ? "TAPE PASS" : "TAPE FAIL");
    return bad;
}
