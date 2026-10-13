// Static data is zeroed by the compiler, whatever the RAM held (prefill: chunk 6 = $AA).
// prefill: AA
// data: x 0000
// data: s 00000000000000000000
// data: t 0500000000
int x;
char s[10];
char t[5] = { 5 };
