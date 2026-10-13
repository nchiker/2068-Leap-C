// The line of a function in image region 2 (region 1 is full of data).
// expect: rterror 4
// rtline: 10
// region: f 2
char big[8192];
int first(void)
{
    return 1;
}
void f(void)
{
    sound(99, 1);
}
int main(void)
{
    f();
    return first();
}
