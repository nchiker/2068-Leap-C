// exit() with the shell's paging (EXROM in): the depth is restored.
// expect: exit 9
// rundepth: 1
// cell: RUNNING 0
int main(void)
{
    exit(9);
    return 0;
}
