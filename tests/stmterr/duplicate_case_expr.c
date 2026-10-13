// expect: error E_DUPCASE 6
enum { A = 65 };
int main(void)
{
    switch ('A') {
    case A: case 'A': ;
    }
    return 0;
}
