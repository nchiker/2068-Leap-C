/* Leap-C hardware check H5: display contention. The loop of H4, its code in image region 4
   ($6000-$77FF, the second display file: memory the display contends), because regions 1-3 are full of
   data. Compare its frames with H4's. */
char a[8192];
char b[4480];
char c[1024];
int main(void)
{
    unsigned i, s = 0, f;
    f = frames();
    for (i = 0; i < 30000; i++)
        s += i ^ (i >> 3);
    f = frames() - f;
    printf("REGION 4: %u FRAMES (%u)", f, s);
    return f;
}
