// expect: error E_NOTSUP 5
struct p { int x; int y; };
int main(void)
{
    struct p v = { 1, 2 };
    return v.x;
}
