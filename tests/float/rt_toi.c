// Float to integer conversions truncate toward 0 and keep the low 16 bits of the integer part (a value
// outside the type's range gives no error: C89 leaves it undefined; Phase 8).
// expect: exit 0
// mem: r+0 ffff 0100 7011 0080 0000 f0d8
int r[6];
float v[6] = { 65535.9, 65537.2, 70000.0, -32768.0, 1e20, -10000.5 };
int main(void)
{
    int i;
    for (i = 0; i < 6; i++)
        r[i] = v[i];
    return 0;
}
