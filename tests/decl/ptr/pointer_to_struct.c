// A struct's pointer type is shared (one TN_PTR node per type).
// tag: node struct size=4 members=next@0:*struct node,v@2:int
// sym: head obj *struct node
// sym: pp obj **struct node
struct node { struct node *next; int v; };
struct node *head;
struct node **pp;
