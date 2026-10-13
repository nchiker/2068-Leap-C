// frames() counts display frames; pause(n) waits n of them (pause(0) returns at once).
// expect: exit 0
unsigned t0, t1, t2;
int main(void)
{
    t0 = frames();
    pause(0);
    t1 = frames();
    pause(5);
    t2 = frames();
    if (t1 - t0 > 1) return 1;
    if (t2 - t1 < 5 || t2 - t1 > 6) return 2;
    return 0;
}
