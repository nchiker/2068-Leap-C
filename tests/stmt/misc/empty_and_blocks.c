// Empty statements, empty blocks, nested blocks with declarations at every level.
// expect: exit 6
int main(void)
{
    int a;
    ;;
    {}
    a = 1;
    {
        int b;
        b = 2;
        {
            int c;
            c = 3;
            {
                ;
                a = a + b + c;
            }
        }
    }
    return a;
}
