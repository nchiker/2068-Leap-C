// sym: a obj [20]char
// sym: b obj [2]char
// sym: c obj [10]char
// sym: d obj [1]char
struct r { int n; char name[20]; struct r *next; } rec, *rp;
char a[sizeof rec.name];
char b[sizeof rp->next];
char c[sizeof rp->next->name / 2];
char d[sizeof rec.name[0]];
