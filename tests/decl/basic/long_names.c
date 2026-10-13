// 31 significant characters: the 32nd and later do not count.
// sym: abcdefghijklmnopqrstuvwxyzABCDE obj char
// sym: x obj [1]char
char abcdefghijklmnopqrstuvwxyzABCDEFGHIJ;
char x[sizeof abcdefghijklmnopqrstuvwxyzABCDEzzzz];
