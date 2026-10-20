// The heap's bounds (spec.md 3.2, 7): one free block from the end of the source (made even) to the
// end mark in the source region's last word ($BFFE). The largest block malloc gives is the heap
// less its 2-byte header: both its ends can be written, one byte more is NULL, and the end mark
// survives (a block allocated after the free is the same block).
// expect: exit 0
int bad;
void ck(int n, int ok) { if (!bad && !ok) bad = n; }
int main(void)
{
    char *p;
    char *q;
    unsigned size;
    p = malloc(1);
    free(p);
    size = 0xBFFEu - (unsigned)p;               /* the free block's data: up to the end mark */
    ck(1, ((unsigned)p & 1) == 0);
    ck(2, malloc(size + 1) == 0);
    q = malloc(size);
    ck(3, q == p);
    q[0] = 1;
    q[size - 1] = 2;
    ck(4, malloc(1) == 0);
    ck(5, *(unsigned *)0xBFFE == 0x8000u);      /* the end mark: a used block of size 0 */
    free(q);
    ck(6, malloc(size) == p);
    ck(7, size > 17000u);
    return bad;
}
