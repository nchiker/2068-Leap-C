// Macros that are strings, characters, keywords' worth of tokens, comments in a replacement.
// expect: exit 0
#define GREETING "hello"
#define LETTER 'q'
#define LOOP for (i = 0; i < 3; i++) /* three times */
#define RET return
int main(void)
{
    char *s;
    int i;
    int n;
    s = GREETING;
    if (s[4] != 'o' || LETTER != 113) return 1;
    n = 0;
    LOOP n++;
    if (n != 3) RET 2;
    RET 0;
}
