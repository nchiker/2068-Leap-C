// 1.0: #undef NULL removes the predefined macro: NULL is then an ordinary identifier.
// expect: exit 5
#undef NULL
int NULL;
int main(void)
{
    NULL = 5;
    return NULL;
}
