// gets(): a line longer than the row continues on the next row; DELETE goes back across the
// row's end.
// expect: exit 0
// keys: "0123456789012345678901234567890XY" DELETE DELETE "Q" ENTER
// screen: 0 0123456789012345678901234567890Q
// screen: 1
// screen: 2 END
char buf[40];
int main(void)
{
    cls();
    gets(buf, 40);
    print("END");
    if (strlen(buf) != 32) return 1;
    if (buf[31] != 'Q') return 2;
    return 0;
}
