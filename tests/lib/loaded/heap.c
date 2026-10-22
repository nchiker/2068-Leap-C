// A loaded library's heap services, LX_MALLOC and LX_FREE, share the heap with malloc() and free()
// (Phase 10): blocks from either can be freed by the other, and a freed block is found again.
// library: testlib
// expect: exit 0
int main(void)
{
    char *a, *b, *c;
    a = t_malloc(100);
    b = malloc(100);
    if (!a || !b || a == b)
        return 1;
    strcpy(a, "LIBRARY");
    strcpy(b, "ROM");
    if (strcmp(a, "LIBRARY") || strcmp(b, "ROM"))
        return 2;
    t_free(a);
    c = malloc(100);
    if (c != a)
        return 3;
    free(c);
    t_free(b);
    if (t_malloc(40000u) != 0)
        return 4;
    t_free(0);
    return 0;
}
