/* Leap-C hardware check H6: floating point, every operation through the EXROM (bank switching). */
float root(float x)
{
    float r = x / 2;
    int i;
    for (i = 0; i < 20; i++)
        r = (r + x / r) / 2;
    return r;
}
int main(void)
{
    float r2 = root(2), r10 = root(10);
    int ok = r2 * r2 > 1.9999 && r2 * r2 < 2.0001 && r10 > 3.1622 && r10 < 3.1623;
    printf("SQRT 2 = %.6f\nSQRT 10 = %.6f\n", r2, r10);
    printf("1/3 = %.9f\n%s", 1.0 / 3, ok ? "FLOAT PASS" : "FLOAT FAIL");
    return ok;
}
