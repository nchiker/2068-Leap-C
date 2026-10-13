// Sibling blocks reuse the same frame bytes; the frame is the deepest use.
// local: x obj int val=2
// local: y obj [8]char val=2
// local: z obj int val=10
// local: outer obj int val=0
// frame: 12
void f(void) {
  int outer;
  { int x; }
  { char y[8]; { int z; } }
}
