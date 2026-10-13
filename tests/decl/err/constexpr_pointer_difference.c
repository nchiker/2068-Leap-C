// expect: error E_CONSTEXPR 3
int arr[10];
enum { D = &arr[5] - &arr[1] };
