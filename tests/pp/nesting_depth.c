// Macros nested 8 deep (the limit).
// expect: exit 8
#define D1 1
#define D2 (D1 + 1)
#define D3 (D2 + 1)
#define D4 (D3 + 1)
#define D5 (D4 + 1)
#define D6 (D5 + 1)
#define D7 (D6 + 1)
#define D8 (D7 + 1)
int main(void) { return D8; }
