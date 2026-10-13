// An implicitly declared function that is never defined.
// expect: error E_UNDEFFN 5
int main(void)
{
    return nowhere(3); /*E*/
}
