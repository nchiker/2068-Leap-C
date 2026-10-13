// expect: error E_UNDEFLABEL 3
int f(void) { lab: return 1; }
int main(void) { goto lab; return 0; }
