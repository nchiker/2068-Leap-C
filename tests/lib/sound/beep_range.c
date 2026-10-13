// beep's semitones -60 to 69 are accepted (below -39 the AY plays its lowest note, A0); 70 is
// runtime error 4 at the calling function's line.
// expect: rterror 4
// rtline: 6
// ay: 0=8 1=0 8=0
void play(void)
{
    beep(1, 70);
}
int main(void)
{
    beep(1, -60);
    beep(1, 69);
    play();
    return 0;
}
