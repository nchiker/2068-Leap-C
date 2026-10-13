// An enum type is int.
// sym: v obj int
// sym: f func fn(int)int
// sym: arr obj [3]int
enum k { K0, K1, K2 };
enum k v;
enum k f(enum k);
enum k arr[K2 + 1];
