// continue in a for loop runs the step.
// expect: exit 25
int main(void)
{
    int i;
    int s;
    s = 0;
    for (i = 0; i < 10; i++) {
        if (i % 2 == 0) continue;
        s += i;
    }
    return s;
}
