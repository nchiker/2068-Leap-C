/* Leap-C hardware check H2: each key pressed, its character and code; ENTER ends. */
int main(void)
{
    int k, n = 0;
    puts("PRESS KEYS; ENTER ENDS");
    while ((k = getkey()) != 13) {
        if (k >= 32 && k < 127)
            printf("%c%4d  ", k, k);
        else
            printf("?%4d  ", k);
        n++;
    }
    return n;
}
