// gets(): DELETE removes the last character (and its echo); DELETE on an empty line does
// nothing; control keys other than ENTER and DELETE are ignored.
// expect: exit 0
// keys: DELETE "ABC" DELETE DELETE 1 4 "Z" ENTER
// screen: 0 AZ
// screen: 1 OK
char buf[10];
int main(void)
{
    cls();
    gets(buf, 10);
    if (strcmp(buf, "AZ") != 0) return 1;
    print("OK");
    return 0;
}
