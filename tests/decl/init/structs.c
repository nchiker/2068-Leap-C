// struct initialisers, nested aggregates with and without braces.
// data: p 0a00 14
// data: q 0100 6162630000 0700
// data: r 0100 0200 0300 0400 0500
// data: s 0900 00
struct pt { int x; char c; } p = { 10, 20 };
struct rec { int id; char name[5]; int k; } q = { 1, "abc", 7 };
struct seg { struct { int x, y; } a, b; int w; } r = { 1, 2, { 3, 4 }, 5 };
struct pt s = { 9 };
