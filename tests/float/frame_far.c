// Float locals beyond (ix+d)'s reach (Phase 8): 30 float locals (150 bytes); the far ones are loaded and
// stored through their address (CG_NEAR), the near ones with F_LDX / F_STX; a float parameter after
// them.
// expect: exit 0
// mem: r+0 822000000082500000008338000000
float r[3];
float far(float p)
{
    float a0, a1, a2, a3, a4, a5, a6, a7, a8, a9;
    float b0, b1, b2, b3, b4, b5, b6, b7, b8, b9;
    float c0, c1, c2, c3, c4, c5, c6, c7, c8, c9;
    a0 = p;
    c9 = a0 * 2;
    b5 = c9 + a0;
    a9 = b5;
    c0 = a9 - 0.5;
    r[0] = c9;
    r[1] = c0;
    c9 += c0;
    return c9;
}
int main(void)
{
    r[2] = far(1.25);
    return 0;
}
