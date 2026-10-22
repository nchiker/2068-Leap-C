// The example library's circle() with a negative radius: runtime error 4 at the line of the program's function
// that called it (Phase 10).
// library: shapes
// expect: rterror 4
// rtline: 6
void draw_it(int r)
{
    circle(100, 100, r);
}
int main(void)
{
    draw_it(10);
    draw_it(-1);
    return 0;
}
