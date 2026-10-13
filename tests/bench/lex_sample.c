/* Lexer throughput sample (M1.1): a realistic Leap-C program of about 2 KB.
   A small "snake" game: globals, structs, arrays, loops, switch, library calls. */
#define W 32
#define H 22
#define MAXLEN 128

struct seg { unsigned char x, y; };

struct seg body[MAXLEN];
int head, len, dir, score;
unsigned seed = 12345u;
char food_x, food_y;
static const char *title = "SNAKE\t2068-LEAP-C";

int rnd(int n)
{
    seed = seed * 75 + 74;          /* linear congruential step */
    return (int)((seed >> 4) % n);
}

void place_food(void)
{
    food_x = (char)rnd(W);
    food_y = (char)(1 + rnd(H - 1));
    at(food_y, food_x);
    putchar('*');
}

int hit_self(int x, int y)
{
    int i, k;
    for (i = 0; i < len - 1; i++) {
        k = (head - i + MAXLEN) & (MAXLEN - 1);
        if (body[k].x == x && body[k].y == y)
            return 1;
    }
    return 0;
}

int step(void)
{
    struct seg *p = &body[head];
    int nx = p->x, ny = p->y;
    switch (dir) {
    case 0: ny--; break;
    case 1: nx++; break;
    case 2: ny++; break;
    default: nx--; break;
    }
    if (nx < 0 || nx >= W || ny < 1 || ny > H || hit_self(nx, ny))
        return 0;
    head = (head + 1) & (MAXLEN - 1);
    body[head].x = (unsigned char)nx;
    body[head].y = (unsigned char)ny;
    at(ny, nx);
    putchar('O');
    if (nx == food_x && ny == food_y) {
        score += 10;
        if (len < MAXLEN - 1) ++len;
        place_food();
    } else {
        struct seg *t = &body[(head - len + MAXLEN) & (MAXLEN - 1)];
        at(t->y, t->x);
        putchar(' ');
    }
    return 1;
}

int main(void)
{
    int key, alive = 1;
    cls();
    puts(title);
    head = 0; len = 3; dir = 1; score = 0;
    body[0].x = 10; body[0].y = 10;
    place_food();
    while (alive) {
        key = inkey();
        if (key == 'q' || key == 'Q') dir = 0;
        else if (key == 'p' || key == 'P') dir = 1;
        else if (key == 'a' || key == 'A') dir = 2;
        else if (key == 'o' || key == 'O') dir = 3;
        alive = step();
        pause(4);
    }
    at(23, 0);
    printf("GAME OVER - SCORE %d\n", score);
    return score;
}
