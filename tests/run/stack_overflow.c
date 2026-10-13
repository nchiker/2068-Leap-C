// Unbounded recursion: ENTER's stack check ends the program with runtime error 1 (stack overflow);
// the harness checks SP, the paging depth and the return to the caller of RT_RUN.
// expect: rterror 1
// noaudit
int down(int n) { return down(n + 1) + 1; }
int main(void) { return down(0); }
