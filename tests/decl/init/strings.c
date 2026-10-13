// char arrays from string literals (spec.md 4.7); adjacent literals concatenate (spec.md 4.1).
// sym: s obj [6]char
// data: s 68656c6c6f00
// sym: t obj [8]char
// data: t 6162630000000000
// sym: u obj [3]char
// data: u 78797a
// sym: v obj [5]char
// data: v 61620a6300
// sym: w obj [4]char
// data: w 61626300
char s[] = "hello";
char t[8] = "abc";
char u[3] = "xyz";
char v[] = "ab" "\n" "c";
char w[] = { "abc" };
