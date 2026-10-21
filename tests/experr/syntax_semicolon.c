// An expression statement without `;`: reported at its own line (Phase 8; was the next token's line).
// expect: error E_SYNTAX 6
int x;
int main(void)
{
    x = 1 /*E*/
    return x;
}
