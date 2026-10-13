// BREAK during a tight loop in chunk 6 ends the program: runtime error 5 at the loop's function,
// with the caller's paging depth, stack and IX restored and the source intact.
// expect: rterror 5
// rtline: 10
// rundepth: 1
// break: after 200000
// breakpc: 0xC000 0xE000
// noaudit
// ay: 8=0 9=0 10=0
void spin(void)
{
    int i;
    for (;;) i++;
}
int main(void)
{
    spin();
    return 0;
}
