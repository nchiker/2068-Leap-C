// mode(1) (hi-res colour) is allowed while the image does not use $6000-$77FF; the end of the
// program restores the normal mode. mode(0) returns to it in the program.
// expect: exit 0
// cell: GFX_MODE 0
int main(void)
{
    mode(1);
    plot(10, 10);
    mode(0);
    mode(1);
    return 0;
}
