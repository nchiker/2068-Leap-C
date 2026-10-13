// expect: error E_DUPCASE 7
int main(void)
{
    switch (1) {
    case 1:
    case 2:
    case 1: ;
    }
    return 0;
}
