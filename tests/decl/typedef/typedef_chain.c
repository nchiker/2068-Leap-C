// sym: A typedef int
// sym: B typedef *int
// sym: C typedef [2]*int
// sym: x obj [5][2]*int
typedef int A;
typedef A *B;
typedef B C[2];
C x[5];
