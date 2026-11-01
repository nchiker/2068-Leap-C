// 1.0: a program may define NULL itself (as its own header would): its definition replaces the predefined one.
// expect: exit 3
#define NULL ((void *)0)
int main(void)
{
    int *p;
    p = NULL;
    return p == 0 ? 3 : 1;
}
