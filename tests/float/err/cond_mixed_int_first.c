// ?: with an integer then a float operand: TYPE MISMATCH, as the other order (spec.md 4.9; Phase 9).
// expect: error E_TYPE 6
int k;
int main(void)
{
    return k ? 2 : 1.5;
}
