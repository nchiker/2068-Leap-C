// mode(1) while the program's image uses $6000-$77FF (image region 4, the hi-res colour file) is
// runtime error 3: here regions 1-3 are full of data, so main's code is in region 4.
// expect: rterror 3
// region: main 4
// rtline: 9
char a[8192];
char b[4480];
char c[1024];
int main(void)
{
    mode(1);
    return 0;
}
