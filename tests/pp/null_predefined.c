// 1.0: NULL is predefined as 0 (a null pointer constant): pointers compare, assign and test against it.
// expect: exit 7
int main(void)
{
    char *p;
    char *q;
    int r;
    p = NULL;
    q = malloc(4);
    r = 0;
    if (p == NULL) r = r + 1;
    if (q != NULL) r = r + 2;
    if (!NULL) r = r + 4;
    free(q);
    return r;
}
