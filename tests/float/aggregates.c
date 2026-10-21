// Floats in structs, arrays (two dimensions) and through pointers (Phase 8): sizes, member offsets,
// pointer arithmetic by 5, a matrix product.
// expect: exit 0
// mem: m+0 8310000000808000000084180000008280000000
// mem: s+0 0700 8100000000828000000070
// mem: c+0 0500 0d00 0100 0200
struct pt { int id; float x; float y; char tag; };
struct pt s = { 7, 1.5, -2.0, 'p' };
float a[2][2] = { { 1.0, 2.0 }, { 3.0, 4.0 } };
float b[2][2] = { { 0.5, -1.0 }, { 2.0, 0.25 } };
float m[2][2];
int c[4];
int main(void)
{
    int i;
    int j;
    int k;
    float *p;
    struct pt *q;
    for (i = 0; i < 2; i++)
        for (j = 0; j < 2; j++) {
            m[i][j] = 0.0;
            for (k = 0; k < 2; k++)
                m[i][j] = m[i][j] + a[i][k] * b[k][j];
        }
    p = &a[0][0];
    q = &s;
    q->x = q->x * 2 + q->y;
    c[0] = sizeof(float);
    c[1] = sizeof(struct pt);
    c[2] = (char *)(p + 1) - (char *)p == 5;
    c[3] = *(p + 1);
    return 0;
}
