// over(1): characters are XORed onto the screen, so printing one twice at the same place clears
// it; over(0) prints opaquely again.
// expect: exit 0
// screen: 0 A C
int main(void)
{
    cls();
    print("ABC");
    over(1);
    at(0, 1);
    print("B");
    over(0);
    return 0;
}
