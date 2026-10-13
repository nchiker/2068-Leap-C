// The largest object: 65535 bytes would exceed the image; the type itself is fine as a pointer.
// sym: p obj *[65535]char
// sym: q obj *[32767][2]char
char (*p)[65535];
char (*q)[32767][2];
