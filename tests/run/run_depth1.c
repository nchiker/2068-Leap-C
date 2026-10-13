// A program run with the EXROM paged in (the shell's state): its code and data in chunk 6 are
// reached with chunk 6 paged out, and the paging is as before afterwards.
// expect: exit 77
// rundepth: 1
int g;
int set(int v) { g = v; return g; }
int main(void) { return set(77); }
