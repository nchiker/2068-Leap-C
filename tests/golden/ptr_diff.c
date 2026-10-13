// Golden: int pointer difference: or a / sbc hl,de, then / 2: ex de,hl / ld hl,2 / call RT_DIVS.
// golden: f DF00 DD6E06DD6607 EB DD6E04DD6605 B7ED52 EB210200CD{RT_DIVS} E7
// expect: exit 0
int f(int *p, int *q) { return p - q; }
int main(void) { return 0; }
