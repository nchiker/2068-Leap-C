// A missing `;` is reported at the line that lacks it, not at the next token's line (Phase 8).
// expect: error E_SYNTAX 7
int main(void)
{
    int x;

    x = 1
    return x;
}
