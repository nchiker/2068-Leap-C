// A cast of a function designator to a pointer type stays the function's address (C89 6.3.4)
// (Phase 9: ROM coverage found the path never compiled).
// expect: exit 7
int seven(void)
{
    return 7;
}
int (*g)(void) = (int (*)(void))seven;
int main(void)
{
    void *p = (void *)seven;
    int (*h)(void) = (int (*)(void))p;
    if (g != h)
        return 1;
    return h();
}
