// data: v 0100 61 0200 62 0300 00
// sym: w obj [2]struct e
// data: w 0500 41 0600 42
struct e { int n; char c; };
struct e v[3] = { { 1, 'a' }, 2, 'b', { 3 } };
struct e w[] = { 5, 'A', 6, 'B' };
