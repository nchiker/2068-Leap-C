// printf's precision above 9 counts as 9 (spec.md 7.1; Phase 9: ROM coverage).
// expect: exit 0
// screen: 0 0.333333333 2.000000000
int main(void)
{
    printf("%.12f %.40f", 1.0 / 3, 2.0);
    return 0;
}
