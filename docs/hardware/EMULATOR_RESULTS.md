# Leap-C hardware kit: the check programs on the emulators (Phase 9, tools/hwkit.py --verify)

Images: HOME e8da395af463cd312d3c5ff415177b95c69e15c77a13c5ae114a978934d5d259, EXROM cef49d740b037f97174b98c63e4f9503a97c09c2466641697a36e6e78e633d8c.

Each program's WAV (tapes/) loaded through the emulator's tape signal input and run. A TS2068 should show Fuse's figures (60 Hz); ZEsarUX 13.0 emulates the TS2068 with a 50 Hz frame. The soak ran 30 emulated minutes on each (ZEsarUX: at 50 Hz, so its frame count is lower).

## H1 `hello.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED hello', 'SOURCE 298 B  FREE 18134 B'), source identical; report ['EXIT 0', 'IMAGE 150 B  HEAP 18130 B']
  - `LEAP-C ON A TS2068`
  - `DIGIT ONE, LETTER L: 1l 1l 11 ll`
  - `CAPITAL I, BAR:      I| I|`
  - `ZERO, CAPITAL O:     0O 0O`
- **Fuse 1.9.1:** LOAD ['LOADED hello', 'SOURCE 298 B  FREE 18134 B'], source identical; report ['EXIT 0', 'IMAGE 150 B  HEAP 18130 B']
  - `LEAP-C ON A TS2068`
  - `DIGIT ONE, LETTER L: 1l 1l 11 ll`
  - `CAPITAL I, BAR:      I| I|`
  - `ZERO, CAPITAL O:     0O 0O`

## H2 `keys.c` (keys)

- **ZEsarUX 13.0:** LOAD ('LOADED keys', 'SOURCE 370 B  FREE 18062 B'), source identical; report ['EXIT 11', 'IMAGE 188 B  HEAP 18058 B']
  - `PRESS KEYS; ENTER ENDS`
  - `a  97  Z  90  5  53  { 123  | 12`
  - `4  } 125  ~ 126  [  91  ]  93  \`
  - `  92  ^  94`
- **Fuse 1.9.1:** LOAD ['LOADED keys', 'SOURCE 370 B  FREE 18062 B'], source identical; report ['EXIT 11', 'IMAGE 188 B  HEAP 18058 B']
  - `PRESS KEYS; ENTER ENDS`
  - `a  97  Z  90  5  53  { 123  | 12`
  - `4  } 125  ~ 126  [  91  ]  93  \`
  - `  92  ^  94`

## H3 `hz60.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED hz60', 'SOURCE 441 B  FREE 17991 B'), source identical; report ['EXIT 600', 'IMAGE 171 B  HEAP 17986 B']
  - `STOPWATCH: FIRST BEEP TO SECOND`
  - `600 FRAMES = 10.0 S AT 60 HZ`
- **Fuse 1.9.1:** LOAD ['LOADED hz60', 'SOURCE 441 B  FREE 17991 B'], source identical; report ['EXIT 600', 'IMAGE 171 B  HEAP 17986 B']
  - `STOPWATCH: FIRST BEEP TO SECOND`
  - `600 FRAMES = 10.0 S AT 60 HZ`

## H4 `cont1.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED cont1', 'SOURCE 432 B  FREE 18000 B'), source identical; report ['EXIT 262', 'IMAGE 188 B  HEAP 17996 B']
  - `REGION 1: 262 FRAMES (29672)`
- **Fuse 1.9.1:** LOAD ['LOADED cont1', 'SOURCE 432 B  FREE 18000 B'], source identical; report ['EXIT 313', 'IMAGE 188 B  HEAP 17996 B']
  - `REGION 1: 313 FRAMES (29672)`

## H5 `cont4.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED cont4', 'SOURCE 516 B  FREE 17916 B'), source identical; report ['EXIT 301', 'IMAGE 13884 B  HEAP 17912 B']
  - `REGION 4: 301 FRAMES (29672)`
- **Fuse 1.9.1:** LOAD ['LOADED cont4', 'SOURCE 516 B  FREE 17916 B'], source identical; report ['EXIT 385', 'IMAGE 13884 B  HEAP 17912 B']
  - `REGION 4: 385 FRAMES (29672)`

## H6 `float.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED float', 'SOURCE 548 B  FREE 17884 B'), source identical; report ['EXIT 1', 'IMAGE 469 B  HEAP 17880 B']
  - `SQRT 2 = 1.414214`
  - `SQRT 10 = 3.162278`
  - `1/3 = 0.333333333`
  - `FLOAT PASS`
- **Fuse 1.9.1:** LOAD ['LOADED float', 'SOURCE 548 B  FREE 17884 B'], source identical; report ['EXIT 1', 'IMAGE 469 B  HEAP 17880 B']
  - `SQRT 2 = 1.414214`
  - `SQRT 10 = 3.162278`
  - `1/3 = 0.333333333`
  - `FLOAT PASS`

## H7 `sound.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED sound', 'SOURCE 394 B  FREE 18038 B'), source identical; report ['EXIT 0', 'IMAGE 130 B  HEAP 18034 B']
  - `A 440 HZ, 2 S`
- **Fuse 1.9.1:** LOAD ['LOADED sound', 'SOURCE 394 B  FREE 18038 B'], source identical; report ['EXIT 0', 'IMAGE 130 B  HEAP 18034 B']
  - `A 440 HZ, 2 S`

## H8 `brk.c` (break)

- **ZEsarUX 13.0:** LOAD ('LOADED brk', 'SOURCE 218 B  FREE 18214 B'), source identical; report ['BREAK', 'LINE 2']
  - `1946`
- **Fuse 1.9.1:** LOAD ['LOADED brk', 'SOURCE 218 B  FREE 18214 B'], source identical; report ['BREAK', 'LINE 2']
  - `757`

## H9 `tapedata.c` (tape)

- **ZEsarUX 13.0:** LOAD ('LOADED tapedata', 'SOURCE 773 B  FREE 17659 B'), source identical; report 'not run here (the cassette suite runs tape_save / tape_load; Fuse runs this one)'
- **Fuse 1.9.1:** LOAD ['LOADED tapedata', 'SOURCE 773 B  FREE 17659 B'], source identical; report ['EXIT 0', 'IMAGE 2468 B  HEAP 17654 B']
  - `RECORD, THEN PRESS ENTER`
  - `REWIND, PLAY, PRESS ENTER`
  - `LOADED 2000 BYTES, 0 WRONG`
  - `TAPE PASS`

## H10 `soak.c` (soak)

- **ZEsarUX 13.0:** LOAD ('LOADED soak', 'SOURCE 1295 B  FREE 17137 B'), source identical; report ['EXIT 0', 'IMAGE 710 B  HEAP 17132 B']
  - `LEAP-C SOAK 15693`
  - `26898 FRAMES`
  - `15694 ROUNDS, SOAK PASS 0`
- **Fuse 1.9.1:** LOAD ['LOADED soak', 'SOURCE 1295 B  FREE 17137 B'], source identical; report ['EXIT 0', 'IMAGE 710 B  HEAP 17132 B']
  - `LEAP-C SOAK 15246`
  - `42469 FRAMES`
  - `15247 ROUNDS, SOAK PASS 0`

## Independent decode

fuse-utils' audio2tape decoded 36 of 36 kit WAVs to exactly their tapes' blocks.
