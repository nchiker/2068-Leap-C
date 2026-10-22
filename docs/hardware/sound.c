/* Leap-C hardware check H7: the AY. A scale from middle C, each note 30 frames (0.5 s at 60 Hz),
   then A above middle C (440 Hz) for 120 frames (2.0 s) for a tuner. */
int main(void)
{
    int n;
    static int scale[8] = {0, 2, 4, 5, 7, 9, 11, 12};
    for (n = 0; n < 8; n++)
        beep(30, scale[n]);
    puts("A 440 HZ, 2 S");
    beep(120, 9);
    return 0;
}
