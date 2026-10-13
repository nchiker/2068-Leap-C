// memcpy, memmove (overlapping both ways), memset and memcmp, with n = 0 and full byte values.
// expect: exit 0
// mem: buf 00 01 02 03 00 01 02 03 04 05 06 07 0c 0d 0e 0f
char buf[16];
char t[8];
int main(void)
{
    int i;
    for (i = 0; i < 16; i++) buf[i] = i;
    if (memmove(buf + 4, buf, 8) != buf + 4) return 1;
    for (i = 0; i < 8; i++)
        if (buf[4 + i] != i) return 2;
    for (i = 0; i < 16; i++) t[i & 7] = 0;
    memcpy(t, buf + 6, 6);
    if (t[0] != 2 || t[5] != 7 || t[6] != 0) return 3;
    memmove(t, t + 1, 5);
    if (t[0] != 3 || t[4] != 7 || t[5] != 7) return 4;
    memmove(t, t, 8);
    memcpy(t, buf, 0);
    if (t[0] != 3) return 5;
    if (memset(t, 0x1FF, 3) != t || t[0] != 255 || t[2] != 255 || t[3] != 6) return 6;
    memset(t, 0, 0);
    if (memcmp(buf, buf, 16) != 0 || memcmp(t, t, 0) != 0) return 7;
    if (memcmp(t, buf, 1) <= 0 || memcmp(buf, t, 1) >= 0) return 8;
    if (memcmp("ab\0c", "ab\0d", 4) >= 0) return 9;
    for (i = 12; i < 16; i++) buf[i] = i;
    return 0;
}
