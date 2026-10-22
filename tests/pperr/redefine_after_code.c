// A macro defined twice after a C identifier: ALREADY DEFINED shows no name (Phase 10: NM held the identifier).
// expect: error E_REDEF 5
int total;
#define N 3
#define N 4
int main(void)
{
    return total + N;
}
