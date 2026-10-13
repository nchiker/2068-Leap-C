// expect: error E_SYNTAX 3
#define A 1
#undef A B
int main(void) { return 0; }
