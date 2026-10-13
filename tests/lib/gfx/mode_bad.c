// mode(n) for n other than 0 and 1 is runtime error 4.
// expect: rterror 4
// rtline: 4
int main(void)
{
    mode(2);
    return 0;
}
