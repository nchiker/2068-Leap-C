// While a library is loaded, image region 3 is closed to the program, as #pragma hires closes region 4
// (Phase 10): an object that region 3 would have held goes to region 4; the library's image is unchanged.
// library: tiny
// region: c 4
// expect: exit 7
char a[8000];
char b[4400];
char c[900];
int main(void)
{
    c[899] = 1;
    return tiny();
}
