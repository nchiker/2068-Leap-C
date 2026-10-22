// A loaded library's own data in image region 3 keeps its values from call to call (t_count); a string in
// the library (a char * result) and a char result (Phase 10).
// library: testlib
// expect: exit 0
// screen: 0 TESTLIB 1 2 3
int main(void)
{
    char c;
    int a, b;
    a = t_count();
    b = t_count();
    printf("%s %d %d %d", t_name(), a, b, t_count());
    c = t_ch(65);
    if (c != 'B' || t_ch(255) != 0)
        return 1;
    return 0;
}
