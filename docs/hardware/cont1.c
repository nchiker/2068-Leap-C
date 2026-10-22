/* Leap-C hardware check H4: display contention, the reference. A loop whose code is in image region 1
   ($C000-$DFFF, chunk 6: memory the display does not contend), timed in frames. Compare with H5. */
int main(void)
{
    unsigned i, s = 0, f;
    f = frames();
    for (i = 0; i < 30000; i++)
        s += i ^ (i >> 3);
    f = frames() - f;
    printf("REGION 1: %u FRAMES (%u)", f, s);
    return f;
}
