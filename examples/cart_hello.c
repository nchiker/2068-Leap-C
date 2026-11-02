// The demo of the runtime cartridge (make cart-demo): a greeting, a computed value, a line.
// On the cartridge it prints:  Hello from a cartridge!  /  Sum of squares 1..10 = 385
int main(void)
{
    int i;
    int sum;

    cls();
    sum = 0;
    for (i = 1; i <= 10; i++)
        sum += i * i;
    printf("Hello from a cartridge!\n");
    printf("Sum of squares 1..10 = %d\n", sum);
    draw(16, 60, 239, 150);
    return 0;
}
