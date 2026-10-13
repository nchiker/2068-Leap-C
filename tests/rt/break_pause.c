// BREAK during pause() ends the program at once (the wait is not a deferred section).
// expect: rterror 5
// rtline: 10
// break: at AY_WAIT_FRAMES 3
// breakpc: AY_WAIT_FRAMES COMP_PLATFORM_END
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
int g;
void wait(void)
{
    pause(30000);
    g = 1;
}
int main(void)
{
    wait();
    return g;
}
