// A local declaration without its `;` (Phase 8: reported at its own line).
// expect: error E_SYNTAX 5
int main(void)
{
    int x
    // a comment line between
    x = 1;
    return x;
}
