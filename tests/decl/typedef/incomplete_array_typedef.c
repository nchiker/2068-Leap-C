// Each object completes its own copy of an incomplete array typedef.
// sym: a obj [2]int
// sym: b obj [3]int
// sym: T typedef []int
typedef int T[];
T a = { 1, 2 };
T b = { 1, 2, 3 };
