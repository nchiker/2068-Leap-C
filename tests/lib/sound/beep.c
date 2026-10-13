// beep(frames, semitone) plays channel A at the semitone's period (110250 / f; middle C: 421)
// through the EXROM trampoline and leaves it silent; 0 frames play nothing.
// expect: exit 0
// ay: 0=165 1=1 8=0
// cell: NOBRK 0
// cell: BANK_EXROM_DEPTH 0
int main(void)
{
    beep(0, 12);
    beep(2, 0);
    return 0;
}
