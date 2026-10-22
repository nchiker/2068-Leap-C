// A loaded library reads the keyboard through the jump table: LX_KEY waits for a key, LX_INKEY returns the key
// latched or 0 (Phase 10).
// library: testlib
// keys: NONE "Q" "z"
// expect: exit 0
int main(void)
{
    if (t_inkey() != 0)
        return 1;
    if (t_key() != 'Q')
        return 2;
    if (getkey() != 'z')
        return 3;
    return 0;
}
