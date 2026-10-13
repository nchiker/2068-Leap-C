// BREAK inside malloc() (its search through many blocks) ends the program; the heap needs no
// repair: the next run starts a fresh one.
// expect: rterror 5
// rtline: 10
// break: after 3000000
// breakpc: LIB_MALLOC LIB_FREE
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
int main(void)
{
    char *p;
    for (;;) {
        p = malloc(4);
        if (p == 0) return 1;
    }
    return 0;
}
