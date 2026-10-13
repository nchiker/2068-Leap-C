// Soak (project_plan.md section 5): mixed library calls from code in chunk 6 for 520 display
// frames, interrupts running throughout; every result is checked (0 failures: exit 0).
// expect: exit 0
// maxi: 200000000
// noaudit
unsigned frames0;
unsigned iterations;
char buf[40];
char num[8];
int main(void)
{
    char *p;
    char *q;
    int x;
    int y;
    frames0 = frames();
    srand(7);
    cls();
    while (frames() - frames0 < 520) {
        iterations++;
        x = rand();
        itoa(x, num, 10);
        if (atoi(num) != x) return 1;
        strcpy(buf, "soak ");
        strcat(buf, num);
        if (strlen(buf) != 5 + strlen(num)) return 2;
        if (strcmp(buf, "soak ") <= 0 || strchr(buf, ' ') != buf + 4) return 3;
        p = malloc(x & 255);
        q = malloc(17);
        if (p == 0 || q == 0) return 4;
        memset(p, 0x5A, x & 255);
        memcpy(q, "seventeen bytes!", 17);
        if (memcmp(q, "seventeen bytes!", 17) != 0) return 5;
        if ((x & 255) && p[(x & 255) - 1] != 0x5A) return 6;
        free(p);
        free(q);
        ink(x & 7);
        at(x % 23, 0);
        print(buf);
        y = (x >> 8) % 192;
        plot(x & 255, y);
        if (!point(x & 255, y)) return 7;
        draw(0, 0, x & 255, (x >> 7) % 192);
        sound(8, 0);
        if (attr(x % 23, 0) != 0x38 + (x & 7)) return 8;
    }
    if (iterations < 50) return 9;
    return 0;
}
