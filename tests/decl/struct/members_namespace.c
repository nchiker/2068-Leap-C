// Member names are per struct; the same name may be a tag, a member and an object.
// tag: x struct size=2 members=x@0:int
// tag: y struct size=1 members=x@0:char
// sym: x obj struct x
struct x { int x; };
struct y { char x; };
struct x x;
