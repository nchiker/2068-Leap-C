// Self-reference through pointers; mutual reference through a forward declaration.
// tag: list struct size=6 members=next@0:*struct list,prev@2:*struct list,val@4:int
// tag: a struct size=4 members=pb@0:*struct b,n@2:int
// tag: b struct size=2 members=pa@0:*struct a
struct list { struct list *next, *prev; int val; };
struct b;
struct a { struct b *pb; int n; };
struct b { struct a *pa; };
