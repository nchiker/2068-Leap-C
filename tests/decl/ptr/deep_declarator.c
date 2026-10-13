// 32 levels of nested declarator parentheses (spec.md 4.10: at least 32 levels).
// sym: x obj *int
// sym: y obj [2][2][2][2][2]char size=32
int (*(((((((((((((((((((((((((((((((x))))))))))))))))))))))))))))))));
char (((((y)[2])[2])[2])[2])[2];
