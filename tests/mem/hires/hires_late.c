// A late #pragma hires cannot take back what is already in region 4: d stays there, nothing else
// goes there, and mode(1) is refused at run time (runtime error 3, the line of main).
// expect: rterror 3
// rtline: 12
// region: d 4
// region: main 1
char a[8100];
char b[4480];
char c[1024];
char d[200];
#pragma hires
int main(void)
{
    d[0] = 1;
    mode(1);
    return 0;
}
