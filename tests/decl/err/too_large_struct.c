// expect: error E_TOOLARGE 4
struct s {
  char a[40000];
  char b[30000];
};
