// Without the library, its function is an undeclared function (C89's implicit declaration): UNDEFINED
// FUNCTION, reported at the end with its name (Phase 10, Fix 2).
// expect: error E_UNDEFFN 6
int main(void)
{
    return t_args(1, 2, 3);
}
