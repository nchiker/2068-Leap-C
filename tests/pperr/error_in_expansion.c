// expect: error E_SYNTAX 5
#define BAD 1 +
int main(void)
{
    return BAD;
}
