// BREAK while a ROM service called by a loaded library runs (LX_KEY waiting for a key): BREAK at the line of the
// program's function that called the library (Phase 10).
// library: testlib
// break: at IO_READ_KEY 2
// breakpc: 0 0x4000
// expect: rterror 5
// rtline: 8
int wait(void)
{
    return t_key();
}
int main(void)
{
    return wait();
}
