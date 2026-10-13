// Nested struct definitions; the inner tag is declared in the enclosing scope (C89).
// tag: outer struct size=7 members=a@0:char,in@1:struct inner,b@5:int
// tag: inner struct size=4 members=x@0:int,y@2:int
// sym: w obj struct inner
struct outer { char a; struct inner { int x, y; } in; int b; };
struct inner w;
