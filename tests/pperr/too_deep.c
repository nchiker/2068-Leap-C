// expect: error E_NESTING 12
#define D1 1
#define D2 D1
#define D3 D2
#define D4 D3
#define D5 D4
#define D6 D5
#define D7 D6
#define D8 D7
#define D9 D8
int main(void)
{ return D9; }
