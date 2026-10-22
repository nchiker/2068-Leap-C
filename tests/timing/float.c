// Timing fixture (Phase 9): float arithmetic, every operation through the EXROM's float core (F_X).
int main(void)
{
    float x = 0, d = 0.5;
    int i;
    for (i = 0; i < 200; i++)
        x = x * 0.99 + d / 3;
    printf("%.4f", x);
    return x * 100;
}
