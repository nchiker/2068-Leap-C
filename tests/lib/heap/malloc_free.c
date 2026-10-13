// malloc/free: blocks do not overlap and keep their data; a freed block is reused (first fit);
// free blocks next to each other join; malloc(0) gives a block; free(NULL) does nothing.
// expect: exit 0
char *p[6];
int main(void)
{
    int i, j;
    char *q, *r;
    for (i = 0; i < 6; i++) {
        p[i] = malloc(10 + i);
        if (p[i] == 0) return 1;
        memset(p[i], 'a' + i, 10 + i);
    }
    for (i = 0; i < 5; i++)
        if (p[i + 1] < p[i] + 10 + i) return 2;
    for (i = 0; i < 6; i++)
        for (j = 0; j < 10 + i; j++)
            if (p[i][j] != 'a' + i) return 3;
    free(p[1]);
    q = malloc(8);
    if (q != p[1]) return 4;
    free(q);
    free(p[2]);
    free(p[3]);
    r = malloc(30);
    if (r != p[1]) return 5;
    for (j = 0; j < 14; j++)
        if (p[4][j] != 'e' || p[5][j] != 'f') return 6;
    if (p[5][14] != 'f') return 8;
    free(0);
    q = malloc(0);
    if (q == 0) return 7;
    return 0;
}
