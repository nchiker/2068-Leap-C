// beep(1, -39): A0, the AY's lowest note (period $FA9: 27.5 Hz from the 1.7645 MHz AY clock).
// expect: exit 0
// ay: 0=0xA9 1=0x0F 8=0
int main(void)
{
    beep(1, -39);
    return 0;
}
