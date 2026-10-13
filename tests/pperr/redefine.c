// expect: error E_REDEF 3
#define A 1
#define A 2
int main(void) { return 0; }
