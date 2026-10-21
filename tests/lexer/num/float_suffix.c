// f, F, l and L suffixes are accepted on floating constants: float, double and long double are one type
// (Phase 8; spec.md 4.9).
// expect: fltx:8140000000 fltx:8140000000 fltx:8140000000 fltx:8140000000 fltx:9143500000 fltx:8000000000
1.5f 1.5F 1.5l 1.5L 1e5f .5L
