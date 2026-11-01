# Leap-C hardware kit: the check programs on the emulators (Phase 9, tools/hwkit.py --verify)

Images: HOME d2b18eaa6b3e100e80b1159aedc3a382a8c7ae552566205dab301739e8f3ef98, EXROM 02790ebe3bf851a749b8ff6810db5bf76bd39518ebda7731b47b4a5239bc4847.

Each program's WAV (tapes/) loaded through the emulator's tape signal input and run. A TS2068 should show Fuse's figures (60 Hz); ZEsarUX 13.0 emulates the TS2068 with a 50 Hz frame. The soak ran 30 emulated minutes on each (ZEsarUX: at 50 Hz, so its frame count is lower).

## H1 `hello.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED hello',), source identical; report ['EXIT 0']
  - `LEAP-C ON A TS2068`
  - `DIGIT ONE, LETTER L: 1l 1l 11 ll`
  - `CAPITAL I, BAR:      I| I|`
  - `ZERO, CAPITAL O:     0O 0O`
- **Fuse 1.9.1:** LOAD ['LOADED hello'], source identical; report ['EXIT 0']
  - `LEAP-C ON A TS2068`
  - `DIGIT ONE, LETTER L: 1l 1l 11 ll`
  - `CAPITAL I, BAR:      I| I|`
  - `ZERO, CAPITAL O:     0O 0O`

## H2 `keys.c` (keys)

- **ZEsarUX 13.0:** LOAD ('LOADED keys',), source identical; report ['EXIT 11']
  - `PRESS KEYS; ENTER ENDS`
  - `a  97  Z  90  5  53  { 123  | 12`
  - `4  } 125  ~ 126  [  91  ]  93  \`
  - `  92  ^  94`
- **Fuse 1.9.1:** LOAD ['LOADED keys'], source identical; report ['EXIT 11']
  - `PRESS KEYS; ENTER ENDS`
  - `a  97  Z  90  5  53  { 123  | 12`
  - `4  } 125  ~ 126  [  91  ]  93  \`
  - `  92  ^  94`

## H3 `hz60.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED hz60',), source identical; report ['EXIT 600']
  - `STOPWATCH: FIRST BEEP TO SECOND`
  - `600 FRAMES = 10.0 S AT 60 HZ`
- **Fuse 1.9.1:** LOAD ['LOADED hz60'], source identical; report ['EXIT 600']
  - `STOPWATCH: FIRST BEEP TO SECOND`
  - `600 FRAMES = 10.0 S AT 60 HZ`

## H4 `cont1.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED cont1',), source identical; report ['EXIT 261']
  - `REGION 1: 261 FRAMES (29672)`
- **Fuse 1.9.1:** LOAD ['LOADED cont1'], source identical; report ['EXIT 313']
  - `REGION 1: 313 FRAMES (29672)`

## H5 `cont4.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED cont4',), source identical; report ['EXIT 301']
  - `REGION 4: 301 FRAMES (29672)`
- **Fuse 1.9.1:** LOAD ['LOADED cont4'], source identical; report ['EXIT 385']
  - `REGION 4: 385 FRAMES (29672)`

## H6 `float.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED float',), source identical; report ['EXIT 1']
  - `SQRT 2 = 1.414214`
  - `SQRT 10 = 3.162278`
  - `1/3 = 0.333333333`
  - `FLOAT PASS`
- **Fuse 1.9.1:** LOAD ['LOADED float'], source identical; report ['EXIT 1']
  - `SQRT 2 = 1.414214`
  - `SQRT 10 = 3.162278`
  - `1/3 = 0.333333333`
  - `FLOAT PASS`

## H7 `sound.c` (run)

- **ZEsarUX 13.0:** LOAD ('LOADED sound',), source identical; report ['EXIT 0']
  - `A 440 HZ, 2 S`
- **Fuse 1.9.1:** LOAD ['LOADED sound'], source identical; report ['EXIT 0']
  - `A 440 HZ, 2 S`

## H8 `brk.c` (break)

- **ZEsarUX 13.0:** LOAD ('LOADED brk',), source identical; report ['BREAK']
  - `2010`
- **Fuse 1.9.1:** LOAD ['LOADED brk'], source identical; report ['BREAK']
  - `723`

## H9 `tapedata.c` (tape)

- **ZEsarUX 13.0:** LOAD ('LOADED tapedata',), source identical; report 'not run here (the cassette suite runs tape_save / tape_load; Fuse runs this one)'
- **Fuse 1.9.1:** LOAD ['LOADED tapedata'], source identical; report ['EXIT 0']
  - `RECORD, THEN PRESS ENTER`
  - `REWIND, PLAY, PRESS ENTER`
  - `LOADED 2000 BYTES, 0 WRONG`
  - `TAPE PASS`

## H10 `soak.c` (soak)

- **ZEsarUX 13.0:** LOAD ('LOADED soak',), source identical; report ['EXIT 0']
  - `LEAP-C SOAK 15766`
  - `27005 FRAMES`
  - `15767 ROUNDS, SOAK PASS 0`
- **Fuse 1.9.1:** LOAD ['LOADED soak'], source identical; report ['EXIT 0']
  - `LEAP-C SOAK 15300`
  - `42465 FRAMES`
  - `15301 ROUNDS, SOAK PASS 0`

## H11 `lib.c` (lib)

- **ZEsarUX 13.0:** LIB ['LIBRARY shapes: 3 FUNCTIONS']; LOAD ('LOADED libcheck',), source identical; report ['EXIT 100']
  - `SHAPES 1 12 255`
  - ` ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░`
  - ` ░                            ░`
  - ` ░          ░░░░░░░░          ░`
  - ` ░        ░░░      ░░░        ░`
  - ` ░       ░░          ░░       ░`
  - ` ░      ░░            ░░      ░`
  - ` ░      ░    ░░░░░░    ░      ░`
  - ` ░     ░░   ░░     ░   ░░     ░`
  - ` ░     ░   ░░       ░   ░     ░`
  - ` ░     ░   ░   ░░   ░   ░     ░`
  - ` ░     ░   ░  ░░░░  ░░  ░     ░`
  - ` ░     ░   ░  ░░░░  ░░  ░     ░`
  - ` ░     ░   ░   ░░   ░   ░     ░`
  - ` ░     ░   ░        ░   ░     ░`
  - ` ░     ░░   ░      ░░  ░░     ░`
  - ` ░      ░    ░░░░░░░   ░      ░`
  - ` ░      ░░     ░░     ░░      ░`
  - ` ░       ░░          ░░       ░`
  - ` ░        ░░░      ░░░        ░`
  - ` ░          ░░░░░░░░          ░`
  - ` ░                            ░`
  - ` ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░`
- **Fuse 1.9.1:** LIB ['LIBRARY shapes: 3 FUNCTIONS']; LOAD ['LOADED libcheck'], source identical; report ['EXIT 100']
  - `SHAPES 1 12 255`
  - ` ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░`
  - ` ░                            ░`
  - ` ░          ░░░░░░░░          ░`
  - ` ░        ░░░      ░░░        ░`
  - ` ░       ░░          ░░       ░`
  - ` ░      ░░            ░░      ░`
  - ` ░      ░    ░░░░░░    ░      ░`
  - ` ░     ░░   ░░     ░   ░░     ░`
  - ` ░     ░   ░░       ░   ░     ░`
  - ` ░     ░   ░   ░░   ░   ░     ░`
  - ` ░     ░   ░  ░░░░  ░░  ░     ░`
  - ` ░     ░   ░  ░░░░  ░░  ░     ░`
  - ` ░     ░   ░   ░░   ░   ░     ░`
  - ` ░     ░   ░        ░   ░     ░`
  - ` ░     ░░   ░      ░░  ░░     ░`
  - ` ░      ░    ░░░░░░░   ░      ░`
  - ` ░      ░░     ░░     ░░      ░`
  - ` ░       ░░          ░░       ░`
  - ` ░        ░░░      ░░░        ░`
  - ` ░          ░░░░░░░░          ░`
  - ` ░                            ░`
  - ` ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░`

## Independent decode

fuse-utils' audio2tape decoded 39 of 39 kit WAVs to exactly their tapes' blocks.
