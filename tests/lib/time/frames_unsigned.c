// frames() returns unsigned: frames() * 0 - 1 is 65535, above 0.
// expect: exit 0
int main(void)
{
    return !(frames() * 0 - 1 > 0);
}
