// expect: error E_UNDEFFN 3
int f(void);
int (*fp)(void) = f;
