// Enumerators count from 0; = resets the count (spec.md 4.2: int constants).
// sym: RED enumc int val=0
// sym: GREEN enumc int val=1
// sym: BLUE enumc int val=10
// sym: CYAN enumc int val=11
// sym: NEG enumc int val=-3
// sym: NEXT enumc int val=-2
// tag: colour enum
// sym: c obj int size=2
enum colour { RED, GREEN, BLUE = 10, CYAN, NEG = -3, NEXT };
enum colour c;
