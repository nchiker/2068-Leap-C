// Macros as case labels and in a switch's controlling expression.
// expect: exit 0
#define ONE 1
#define TWO 2
#define SEL (ONE + TWO)
int main(void)
{
    switch (SEL) {
    case ONE: return 1;
    case TWO: return 2;
    case ONE + TWO: return 0;
    }
    return 3;
}
