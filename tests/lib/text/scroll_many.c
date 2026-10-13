// 40 lines through the bottom of the screen: each new line scrolls it up; the last 24 remain.
// expect: exit 0
// screen: 0 LINE 17
// screen: 22 LINE 39
// screen: 23 END
int main(void)
{
    int i;
    cls();
    for (i = 0; i < 40; i++)
        printf("LINE %d\n", i);
    print("END");
    return 0;
}
