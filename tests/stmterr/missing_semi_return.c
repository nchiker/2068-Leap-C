// A missing `;` after a return value, the `}` on the next line (Phase 8).
// expect: error E_SYNTAX 5
int main(void)
{
    return 0 /* the ; is missing */
}
