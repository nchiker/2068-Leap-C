# 2068-Leap-C -- User's Manual

The full user's manual is in eight parts, written in the style of the Sinclair QL User Guide (as the 2068-Leap V2 manual is):

| Part | |
|---|---|
| [1. Introduction](manual/01_introduction.md) | what Leap-C is, how to start it, how to read the manual |
| [2. Beginner's guide](manual/02_beginners_guide.md) | a course in C from nothing: the editor, a first program, numbers, characters, decisions, loops, functions, arrays, pointers, structures, the screen, graphics, sound, the keyboard, floating point, tapes |
| [3. Keywords](manual/03_keywords.md) | every C keyword, preprocessor directive, operator and shell command, A to Z |
| [4. The library](manual/04_library.md) | every built-in function, A to Z |
| [5. Concepts](manual/05_concepts.md) | arrays, BREAK, conversions, differences from standard C, errors, floating point, memory, pointers, tapes, the editor ... A to Z |
| [6. Loadable libraries](manual/06_libraries.md) | `LIB`, the shapes library, writing your own |
| [7. Practical examples](manual/07_examples.md) | complete programs |
| [Appendices](manual/08_appendices.md) | reports, compile and runtime error codes, character set and keyboard, limits, memory map, hardware notes, index |

Also: the shorter [user guide](USER_GUIDE.md); a Word edition, [2068_Leap-C_Users_Manual.docx](2068_Leap-C_Users_Manual.docx) and [.doc](2068_Leap-C_Users_Manual.doc) (`make manual`).

Every program in the manual with `// expect:` lines is a test: `tools/docexamples.py` generates it into `tests/doc/manual_*.c` and the executable corpus runs it on the ROM (`make check` keeps the two in step).
