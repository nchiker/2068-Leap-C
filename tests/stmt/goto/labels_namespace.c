// Labels have their own name space: a label and a variable of the same name.
// expect: exit 2
int main(void)
{
    int x;
    x = 0;
x:
    x++;
    if (x < 2) goto x;
    return x;
}
