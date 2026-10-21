// A file-scope declaration without its `;` (Phase 8: reported at its own line).
// expect: error E_SYNTAX 3
int g
int main(void)
{
    return 0;
}
