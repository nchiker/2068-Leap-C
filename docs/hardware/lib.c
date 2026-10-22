/* H11: a library loaded from tape (Phase 10). First LIB "shapes" (the kit's tapes/l1_shapes: the example
   library, libs/shapes.asm): LIBRARY shapes: 3 FUNCTIONS. Then LOAD "" this program and RUN it: a box with
   three circles in it, row 0 "SHAPES 1 12 255", EXIT 100. Without the library, RUN reports
   ERROR 70: UNDEFINED FUNCTION, naming one of the library's functions. */
int main(void)
{
    int r;
    cls();
    box(8, 8, 247, 183);
    for (r = 10; r <= 70; r += 30)
        circle(128, 96, r);
    printf("SHAPES %u %u %u", isqrt(2), isqrt(144), isqrt(65535u));
    return isqrt(10000);
}
