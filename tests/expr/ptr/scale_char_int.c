// Pointer arithmetic scales by the element size: char (1) and int (2); the address in memory.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
char cs[8];
int is[8];
int main(void)
{
    char *pc;
    int *pi;
    pc = cs;
    pi = is;
    ck(1, (int)(pc + 3) - (int)cs, 3);
    ck(2, (int)(pi + 3) - (int)is, 6);
    pc += 2; pi += 2;
    ck(3, (int)pc - (int)cs, 2);
    ck(4, (int)pi - (int)is, 4);
    pi = pi - 1;
    ck(5, (int)pi - (int)is, 2);
    ck(6, (int)(3 + pi) - (int)is, 8);
    pc = &cs[7];
    ck(7, pc - cs, 7);
    pi = &is[6];
    ck(8, pi - is, 6);
    ck(9, &is[1] - pi, -5);
    return bad;
}
