// Golden: A byte stored through a pointer: ld a,l / ld (de),a.
// golden: f DF00 DD6E04DD6605 EB DD6E062600 7D12 E7
// expect: exit 0
void f(char *p, char v) { *p = v; }
int main(void) { return 0; }
