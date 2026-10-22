// A static object declared twice at file scope (C89 6.7.2: a tentative definition, then the definition):
// one object (Phase 9: ROM coverage).
// expect: exit 5
static int x;
static int x = 5;
int main(void)
{
    return x;
}
