// Golden: A frame object more than 128 bytes below IX: push ix / pop hl / ld bc,d / add hl,bc.
// golden: f DFCA DDE5E10136FF09 EB210100 D7 DDE5E10136FF09 CF E7
// expect: exit 0
int f(void) { char pad[200]; int x; x = 1; return x; }
int main(void) { return 0; }
