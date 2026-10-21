// A `)` missing at the end of a line is reported there, not at the `{` on the next line (Phase 8).
// expect: error E_SYNTAX 5
int main(void)
{
    if (1 > 0
    {
        return 0;
    }
    return 1;
}
