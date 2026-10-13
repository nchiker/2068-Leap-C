// Golden: i++ as a value: inc hl / store / dec hl (the old value).
// golden: f DF02 210000DD75FEDD74FF DD6EFEDD66FF 23 DD75FEDD74FF 2B E7
// expect: exit 0
int f(void) { int i; i = 0; return i++; }
int main(void) { return 0; }
