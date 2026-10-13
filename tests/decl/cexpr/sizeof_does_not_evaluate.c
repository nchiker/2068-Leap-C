// A string literal under sizeof is not stored; the [] count pass stores nothing either
// (n is allocated, then "a" at $DFF2 and "bc" at $DFEF, then z).
// sym: a obj [6]char val=0xDFFA
// addr: x 0xDFF8
// sym: n obj [2]*char val=0xDFF4
// addr: z 0xDFED
char a[sizeof "hello"];
int x;
char *n[] = { "a", "bc" };
int z;
