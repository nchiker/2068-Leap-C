// outp(port, value) and inp(port): the AY's register select ($F5) and data ($F6) ports, read back.
// expect: exit 0
// ay: 3=5
int main(void)
{
    outp(0xF5, 3);
    outp(0xF6, 0x105);
    outp(0xF5, 3);
    if (inp(0xF6) != 5) return 1;
    outp(0xF5, 7);
    outp(0xF6, 0x3F);
    if (inp(0xFFF6) != 0x3F) return 2;
    return 0;
}
