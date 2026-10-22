// A loaded library's integer helpers (Phase 10): LX_DIVS (signed, truncated toward zero), LX_DIVU (unsigned,
// the quotient and the remainder), as / and % compute them; division by 0 gives 0.
// library: testlib
// expect: exit 0
int main(void)
{
    if (t_divs(17, 5) != 3 || t_divs(-17, 5) != -3 || t_divs(17, -5) != -3 || t_divs(-17, -5) != 3)
        return 1;
    if (t_divu(60000u, 7) != 8571u || t_modu(60000u, 7) != 3)
        return 2;
    if (t_divu(65535u, 256) != 255 || t_modu(65535u, 256) != 255)
        return 3;
    if (t_divs(5, 0) != 0 || t_divu(5, 0) != 0 || t_modu(5, 0) != 0)
        return 4;
    if (t_divs(-32768, -1) != -32768)
        return 5;
    return 0;
}
