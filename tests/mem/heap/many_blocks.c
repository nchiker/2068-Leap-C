// The heap at its limit with small blocks: allocate 16-byte blocks until malloc gives NULL; every
// block lies inside the heap ($7800-$BFFD), none overlaps the next, and after freeing all of them
// one block of the whole heap fits again (the free blocks are joined as malloc passes them).
// expect: exit 0
int bad;
void ck(int n, int ok) { if (!bad && !ok) bad = n; }
char *blk[1200];
int main(void)
{
    int n;
    int i;
    char *first;
    n = 0;
    while (n < 1200 && (blk[n] = malloc(16)) != 0)
        n++;
    ck(1, n > 900);
    ck(2, n < 1200);
    first = blk[0];
    for (i = 0; i < n; i++) {
        ck(3, (unsigned)blk[i] >= 0x7800u && (unsigned)blk[i] + 16 <= 0xBFFEu);
        if (i > 0)
            ck(4, blk[i] == blk[i - 1] + 18);
        blk[i][0] = i;
        blk[i][15] = i;
    }
    for (i = 0; i < n; i++)
        ck(5, blk[i][0] == (char)i && blk[i][15] == (char)i);
    for (i = 0; i < n; i++)
        free(blk[i]);
    ck(6, malloc(0xBFFEu - (unsigned)first) == first);
    return bad;
}
