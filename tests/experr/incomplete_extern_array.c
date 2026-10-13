// An extern array of unknown size has no storage until its definition: using it earlier is an error in Leap-C.
// expect: error E_INCOMPLETE 6
extern int a[];
int main(void)
{
    return a[1]; /*E*/
}
int a[4];
