// printf has no prototype (its arguments are variadic): any number of arguments, chars promoted.
// expect: exit 0
// screen: 0 plain
// screen: 1 1 2 3 4 5 6 7 8 A
int main(void)
{
    char c;
    c = 'A';
    cls();
    printf("plain\n");
    printf("%d %d %d %d %d %d %d %d %c", 1, 2, 3, 4, 5, 6, 7, 8, c);
    return 0;
}
