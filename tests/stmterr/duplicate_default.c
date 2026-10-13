// expect: error E_DUPCASE 7
int main(void)
{
    switch (1) {
    default:
    case 2: ;
    default: ;
    }
    return 0;
}
