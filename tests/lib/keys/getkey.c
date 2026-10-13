// getkey() waits for a key and returns its code (the keys come through the ISR's latch).
// expect: exit 0
// keys: "Az" 13 8
int main(void)
{
    if (getkey() != 'A') return 1;
    if (getkey() != 'z') return 2;
    if (getkey() != 13) return 3;
    if (getkey() != 8) return 4;
    return 0;
}
