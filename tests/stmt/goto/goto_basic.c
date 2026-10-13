// goto forward and backward, across blocks, a label at the end of a block.
// expect: exit 0
int main(void)
{
    int i;
    int n;
    i = 0;
    n = 0;
again:
    i++;
    if (i < 5) goto again;
    if (i != 5) return 1;
    goto skip;
    n = 99;
skip:
    {
        int k;
        k = 3;
        if (k == 3) goto inner;
        n = 98;
    inner:
        n += k;
    }
    if (n != 3) return 2;
    goto end;
    return 3;
end:
    ;
    return 0;
}
