// A case label must be an integer constant.
// expect: error E_CONSTEXPR 8
int main(void)
{
    int k;
    k = 1;
    switch (k) {
    case 1.5:
        return 1;
    }
    return 0;
}
