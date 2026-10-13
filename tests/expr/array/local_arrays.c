// Local arrays in the frame: indexing, decay to pointers, char and int elements, sizeof.
// expect: exit 0
int bad;
void ck(int n, int got, int want) { bad = bad ? bad : got == want ? 0 : n; }
int sum3(int *v) { return v[0] + v[1] + v[2]; }
int main(void)
{
    int a[3];
    char s[4];
    int k;
    k = 1;
    a[0] = 10; a[k] = 20; a[k + 1] = 30;
    ck(1, sum3(a), 60);
    s[0] = 'a'; s[1] = s[0] + 1; s[2] = 0;
    ck(2, s[1], 'b');
    ck(3, sizeof a, 6);
    ck(4, &a[2] - a, 2);
    ck(5, *(a + 1), 20);
    return bad;
}
