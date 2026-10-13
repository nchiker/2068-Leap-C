// gets(): printable characters are stored and echoed at the print position; ENTER ends the line
// with a new line and a NUL; the result is the buffer.
// expect: exit 0
// keys: "Hello, C" ENTER
// screen: 0 > Hello, C
// screen: 1 NEXT
char buf[20];
int main(void)
{
    cls();
    print("> ");
    if (gets(buf, 20) != buf) return 1;
    print("NEXT");
    if (strcmp(buf, "Hello, C") != 0) return 2;
    if (buf[8] != 0) return 3;
    return 0;
}
