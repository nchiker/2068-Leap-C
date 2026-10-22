/* Leap-C hardware check H3: the frame rate. Time from the first beep to the second with a stopwatch:
   600 frames are 10.0 s at 60 Hz (12.0 s on a 50 Hz machine). */
int main(void)
{
    unsigned f0, f1;
    puts("STOPWATCH: FIRST BEEP TO SECOND");
    beep(6, 12);
    f0 = frames();
    pause(600);
    f1 = frames();
    beep(6, 12);
    printf("%u FRAMES = 10.0 S AT 60 HZ", f1 - f0);
    return f1 - f0;
}
