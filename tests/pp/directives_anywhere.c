// Directives between statements, between the tokens of a declaration, inside a function; #undef
// and a new definition; `#` alone; #include of the built-in header.
// expect: exit 0
#include <leap.h>
#include "leap.h"
#
int g
#define G_INIT 41
= G_INIT + 1;
int h =
#define H 3
H;
int main(void)
{
    int r;
#define R 5
    r = R;
#undef R
#define R 6
    r += R;
#undef R
    {
        int R;
        R = 2;
        r += R;
    }
#undef NEVER_DEFINED
    if (g != 42) return 1;
    if (h != 3) return 2;
    return r - 13;
}
