// sym: Point typedef struct pt
// sym: Node typedef struct{v:int,next:*struct nd}
// sym: a obj [3]struct pt size=12
typedef struct pt { int x, y; } Point;
typedef struct { int v; struct nd *next; } Node;
Point a[3];
