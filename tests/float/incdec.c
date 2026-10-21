// ++ and -- on float objects (Phase 8): prefix gives the new value, postfix the old one (kept
// exactly: F_OLD), on a global, a local, a parameter, an array element and a member through a pointer.
// expect: exit 0
// mem: r+0 82000000008200000000820000000082000000008100000000
// mem: r+25 82400000000000000000820000000081000000005f5be6fecf
// mem: v+0 81200000008000000000
// mem: c+0 0100010001000100
struct p { int n; float f; } s = { 0, 1.0 };
float r[10];
float v[2] = { 0.25, -0.5 };
int c[4];
float g = 1.0;
float post(float a)
{
    a++;
    return a++;
}
int main(void)
{
    float l;
    float *q;
    struct p *ps;
    int i;
    l = 2.0;
    i = 0;
    r[i++] = ++g;
    r[i++] = g--;
    r[i++] = l++;
    r[i++] = --l;
    q = v;
    ++q[0];
    v[1]++;
    ps = &s;
    r[i++] = ps->f++;
    r[i++] = ++ps->f;
    r[i++] = --g;
    r[i++] = post(1.0);
    c[0] = g == 0.0;
    c[1] = l == 2.0;
    c[2] = ps->f == 3.0;
    c[3] = (int)post(0.5);
    r[i++] = 1e-10;
    r[i] = r[i - 1]++;
    return (r[i] == 1e-10 && r[i - 1] == 1.0) ? 0 : 1;
}
