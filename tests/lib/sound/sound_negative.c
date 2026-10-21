// sound: a negative register is runtime error 4 (registers 0-15).
// expect: rterror 4
int main(void)
{
    sound(-1, 0);
    return 0;
}
