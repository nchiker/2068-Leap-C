// Float initialisers (Phase 8): floating constant expressions folded by the float core, integers
// converted; integer objects from floating constants truncated toward zero.
// data: a 8140000000
// data: b 81c0000000
// data: c 8240000000
// data: e 8300000000
// data: h 8200000000
// data: k 0000000000
// data: z 0000000000
// data: arr 81000000008220000000 0000000000
// data: s 07008140000000
// data: i 0200
// data: j feff
// data: ch 41
// data: u 409c
// data: v ffff
// data: w 0300
float a = 1.5;
float b = -1.5;
double c = 3;
float e = 1.5 * 2 + 1;
float h = 10 / 4;
float k = 0;
float z;
float arr[3] = { 1, 2.5 };
struct { int n; float x; } s = { 7, 1.5 };
int i = 2.9;
int j = -2.9;
char ch = 65.5;
unsigned u = 40000.0;
unsigned v = -1.0;
int w = (int)3.75;
