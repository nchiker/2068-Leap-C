// First fit over the image regions in order (spec.md 3.2): region 1 ($C000-$DFFF), region 2
// ($E000-$F17F), ...
// addr: a 0xC0C0
// addr: b 0xF054
// addr: c 0xC05C
char a[8000];
char b[300];
char c[100];
