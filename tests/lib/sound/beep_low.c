// beep: below -39 (A0) the AY plays A0: -50 gives the same tone registers as -39.
// expect: exit 0
// ay: 0=0xA9 1=0x0F 8=0
int main(void)
{
    beep(1, -50);
    return 0;
}
