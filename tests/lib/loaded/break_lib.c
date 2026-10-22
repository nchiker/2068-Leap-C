// BREAK while a loaded library's own code runs (its loop in image region 3): the program ends with BREAK at
// the line of the program's function that called the library, as BREAK in the ROM's library does
// (RT_BREAKREQ: image region 3 holds no program code while a library is loaded; Phase 10).
// library: testlib
// break: at lib:spin_loop 3
// breakpc: lib:spin_loop lib:spin_end
// expect: rterror 5
// rtline: 9
int work(void)
{
    return t_spin(30000);
}
int main(void)
{
    puts("SPIN");
    return work();
}
