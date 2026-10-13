// Every run starts with an empty heap: the same requests give the same blocks.
// expect: exit 0
int main(void)
{
    char *a;
    char *b;
    a = malloc(50);
    b = malloc(50);
    if (a == 0 || b != a + 52) return 1;
    return 0;
}
