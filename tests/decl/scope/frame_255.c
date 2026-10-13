// A frame of exactly 255 bytes is allowed (spec.md 4.10).
// local: big obj [253]char flags=auto val=0
// local: last obj int flags=auto val=253
// frame: 255
void f(void) { char big[253]; int last; }
