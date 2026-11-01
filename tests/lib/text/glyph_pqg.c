// The glyphs of p, q and g sit on the x-height: rows 0-1 empty, the bowl in rows 2-5, the descender
// in rows 6-7 (platform delta D24; V2's started the bowl a row higher, nchiker/2068-Leap#6). The screen
// bytes of "pqg" printed at row 0 match the glyph table. A mismatch returns 10 * (character + 1) + row.
// expect: exit 0
int hex(char c)
{
    if (c >= 'A')
        return c - 'A' + 10;
    return c - '0';
}

int main(void)
{
    char *want;
    unsigned char *scr;
    int c, r, b;
    want = "0000F08888F0808000007888887808080000788888780870";
    cls();
    print("pqg");
    for (c = 0; c < 3; c++)
        for (r = 0; r < 8; r++) {
            scr = (unsigned char *)(0x4000 + r * 256 + c);
            b = hex(want[c * 16 + r * 2]) * 16 + hex(want[c * 16 + r * 2 + 1]);
            if (*scr != b)
                return 10 * (c + 1) + r;
        }
    return 0;
}
