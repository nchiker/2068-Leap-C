// #include <leap.h> is accepted and changes nothing; library functions in every statement form.
// expect: exit 6
#include <leap.h>
#include "leap.h"
int main(void)
{
    int n;
    n = 0;
    while (strlen("abc") > n) n++;
    switch (abs(-3)) { case 3: n = n + 3; }
    return n;
}
