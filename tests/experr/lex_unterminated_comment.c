// An unterminated comment is reported at the line where it starts (Phase 6: the cursor goes there).
// expect: error E_COMMENT 4
int main(void)
{   /* never
       closed
    return 0;
}
