// A loaded library reads the frame counter (LX_FRAMES): it counts the frames pause() waits, as frames() does
// (Phase 10).
// library: testlib
// expect: exit 0
int main(void)
{
    unsigned a, b;
    a = t_frames();
    pause(5);
    b = t_frames();
    if (b - a < 5 || b - a > 6)
        return 1;
    if (frames() - b > 1)
        return 2;
    return 0;
}
