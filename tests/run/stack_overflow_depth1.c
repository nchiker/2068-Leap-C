// A stack overflow while the shell had the EXROM paged in: the paging is restored (depth 1).
// expect: rterror 1
// rundepth: 1
// noaudit
int down(int n) { return down(n + 1); }
int main(void) { return down(0); }
