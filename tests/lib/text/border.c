// border(n) sets the border colour n & 7 (the port $FE shadow keeps the other bits).
// expect: exit 0
// cell: PORT_FE_SHADOW 0x05
int main(void)
{
    border(2);
    border(13);
    return 0;
}
