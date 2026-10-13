// goto out of nested loops; labels in two functions with the same names.
// expect: exit 0
int find(int target)
{
    int i;
    int j;
    for (i = 0; i < 10; i++)
        for (j = 0; j < 10; j++)
            if (i * 10 + j == target) goto found;
    return -1;
found:
    return i * 100 + j;
}
int other(void)
{
    goto found;
found:
    return 1;
}
int main(void)
{
    if (find(57) != 507) return 1;
    if (find(100) != -1) return 2;
    return other() - 1;
}
