// sound(reg, value) writes an AY register (value & 255). The end of the program silences the
// three channels (volumes R8-R10 = 0); the other registers keep their values.
// expect: exit 0
// ay: 0=200 1=3 2=77 7=56 8=0 9=0 10=0 13=4
int main(void)
{
    sound(0, 200);
    sound(1, 3);
    sound(2, 256 + 77);
    sound(7, 0x38);
    sound(8, 15);
    sound(9, 12);
    sound(10, 16);
    sound(13, 4);
    return 0;
}
