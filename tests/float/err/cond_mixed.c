// ?: with a float and an integer operand: TYPE MISMATCH (deviation: cast one; spec.md 4.9).
// expect: error E_TYPE 6
int k;
int main(void)
{
    return k ? 1.5 : 2;
}
