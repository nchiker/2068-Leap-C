// A pointer parameter refuses an int (and an int parameter refuses a pointer).
// expect: error E_TYPE 7
char buf[4];
int main(void)
{
    strcpy(buf, "a");
    strcpy(buf, 5);
    return 0;
}
