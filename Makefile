# 2068-Leap-C build (project_plan.md section 3 onwards: Phase 1 M1.1-M1.3, Phases 2-10).
#   make / make build   production images in build/, test images (-DLEAPC_TEST) in build/test/, the libraries
#   make libs           Phase 10: the loaded libraries (the example libs/shapes.asm, the test libraries
#                       tests/libs/*.asm) as image, labels, .tap, .tzx and .wav in build/libs/ (tools/lib2tape.py)
#   make check          strict assembly (build), budgets, platform delta check, test-image check,
#                       RAM layout guard (static census of the RAM the ROMs reference, with negative
#                       controls), documentation examples in step with tests/doc/ (tools/docexamples.py)
#   make budget         per-component budget table and ROM map
#   make inventory      every HOME routine, table and gap with its referrers (docs/HOME_ROM_INVENTORY.md)
#   make test           ZEsarUX tests on the images (boot, lexer, declarations, executable C programs:
#                       expressions, statements, preprocessor, the library, runtime errors, BREAK,
#                       soak, floating point, the documentation's examples; the float core against its
#                       model; helper, library, ISR, lexer and spike-workload measurements; memory
#                       layout, regions, stack, heap, banking invariants; the shell; the compile/run
#                       workflow: typed programs, the corpus through RUN, diagnostics, reports; the
#                       cassette: SAVE/LOAD/VERIFY and tape_save/tape_load on real tape signals, V2's
#                       tapes; Phase 9: boots from power-on RAM patterns) and the canary, as tasks on a pool
#                       of emulators, with ZEsarUX's code coverage (build/coverage.json, reported by
#                       tools/romcov.py in build/romcov.md); needs ts2068-debug, ZEsarUX 13.0 with the EXROM patch,
#                       and 2068-Leap (read only) for the V2 reference ROM (where: CONTRIBUTING.md, LEAPC_* variables)
#   make test-fast      the development subset (Phase 8): make test without the cassette suite, the corpus
#                       through the shell's RUN and the typing-cost/redraw measurements, the canary over
#                       every other program; about a fifth of make test's time. make test stays the gate
#   make canary         the RAM canary and banking invariants over the whole corpus (4 emulators)
#   make fuse           Phase 9: the production ROMs on Fuse 1.9.1, headless (tools/fusetest.py: boot, keyboard,
#                       typed programs, BREAK, SAVE, a WAV, the corpus LOADed from tape and RUN)
#   make timing         Phase 9: the same programs timed on ZEsarUX and Fuse (tools/timingcmp.py, build/timing.md)
#   make poweron        Phase 9: the boot from power-on RAM patterns, a corpus slice from each (also in make test)
#   make kit            Phase 9: the hardware kit in build/kit: EPROM images (27128 HOME, 2764 EXROM) with
#                       checksums, the hardware check programs and examples as .tap/.tzx/.wav (tools/hwkit.py)
#   make capacity       the measured capacity table (build/capacity.json, docs/milestones/M4.md)
#   make repro          two clean builds must give identical image hashes
#   make release        Phase 11: the release assets in build/release (tools/release.py): the emulator pack and the
#                       hardware kit as zips, with SHA256SUMS
#   make tapetol        Phase 11 (M11-tape): the tape receiver's tolerance envelope on Fuse (tools/tapetol.py), the
#                       beta.1 images (build/beta1, tools/beta1ref.sh: the tag through `git archive`) against the
#                       current ones: every case beta.1 accepts must still be accepted
#   make provenance     Phase 11 (M11-tape): the images compared with the stock ROMs ($LEAPC_STOCK_ROMS; also in
#                       make check when they are there): no common run of 12 bytes or more unless recorded
#   make audit          z80-skills pattern scan of src/ (hints for the manual audit, not a gate)
#   make v2ref          the V2 reference ROM (tag v2.0.1-emu.1) in build/v2ref/, built from the frozen
#                       repository through `git archive` (the cross-version tape tests)
# Host tool: tools/c2tape.py FILE.c OUT.tap|OUT.tzx makes a program tape that LOAD reads.
.PHONY: all build prod testimg libs check budget inventory test test-fast canary capacity repro audit v2ref clean \
	fuse timing poweron kit qualify release tapetol provenance

ASM := tools/sjasm_strict.sh
SKILLS ?= $(HOME)/z80-skills/skills

all: build

build: prod testimg libs

prod:
	mkdir -p build
	python3 tools/gen_diag.py build/diag_text.inc
	$(ASM) --sym=build/leapc_home.sym --lst=build/leapc_home.lst src/rom/home.asm
	python3 tools/gen_exports.py build/leapc_home.sym src/rom/home_exports.txt build/home_exports.inc
	$(ASM) --sym=build/leapc_exrom.sym --lst=build/leapc_exrom.lst src/rom/exrom.asm
	cat build/leapc_home.bin build/leapc_exrom.bin > build/leapc_zesarux.bin
	tools/make_dck.sh build/leapc_exrom.bin build/leapc_exrom.dck
	cd build && sha256sum leapc_home.bin leapc_exrom.bin leapc_zesarux.bin leapc_exrom.dck > SHA256SUMS

testimg:
	mkdir -p build/test
	python3 tools/gen_diag.py build/diag_text.inc
	$(ASM) -DLEAPC_TEST --sym=build/test/leapc_home.sym --lst=build/test/leapc_home.lst src/rom/home.asm
	python3 tools/gen_exports.py build/test/leapc_home.sym src/rom/home_exports.txt build/test/home_exports.inc
	$(ASM) -DLEAPC_TEST --sym=build/test/leapc_exrom.sym --lst=build/test/leapc_exrom.lst src/rom/exrom.asm
	cat build/test/leapc_home.bin build/test/leapc_exrom.bin > build/test/leapc_zesarux.bin

LIBS := libs/shapes tests/libs/testlib tests/libs/tiny

libs:
	mkdir -p build/libs
	for l in $(LIBS); do n=$$(basename $$l); \
		python3 tools/lib2tape.py $$l.asm build/libs/$$n.bin build/libs/$$n.sym build/libs/$$n.tap \
			build/libs/$$n.tzx build/libs/$$n.wav || exit 1; done
	cd build/libs && sha256sum *.bin *.tap *.tzx *.wav > SHA256SUMS

check: build
	python3 tools/budget.py --check --json build/budget.json
	python3 tools/check_platform.py
	python3 tools/check_test_image.py
	python3 tools/check_ram_layout.py
	python3 tools/check_ram_layout.py --negative
	python3 tools/docexamples.py --check
	python3 tools/provenance.py; r=$$?; [ $$r -eq 0 ] || [ $$r -eq 2 ]

budget: prod
	python3 tools/budget.py

inventory: prod
	python3 tools/rom_inventory.py

test: build build/v2ref/ts2068rom_zesarux.bin
	python3 tools/run_tests.py --coverage build/coverage.json
	python3 tools/romcov.py build/coverage.json

test-fast: build
	python3 tools/run_tests.py --fast --json build/test_fast_results.json

v2ref: build/v2ref/ts2068rom_zesarux.bin

build/v2ref/ts2068rom_zesarux.bin:
	tools/v2ref.sh

canary: build
	python3 tools/canary.py

fuse: build
	python3 tools/fusetest.py

timing: build
	python3 tools/timingcmp.py

poweron: build
	python3 tools/run_tests.py --suite poweron --json build/poweron_results.json

kit: build
	python3 tools/hwkit.py

release: kit
	python3 tools/release.py

capacity: build
	python3 tools/capacity.py

repro:
	tools/check_repro.sh

# The Phase 9 qualification, every suite in sequence (about 70 minutes); then make repro.
qualify: build
	tools/qualify.sh

tapetol: prod build/beta1/leapc_home.bin
	python3 tools/tapetol.py --build build/beta1 --build build

build/beta1/leapc_home.bin:
	tools/beta1ref.sh

provenance: prod
	python3 tools/provenance.py

audit:
	mkdir -p build
	python3 $(SKILLS)/audit-z80/scripts/z80_pattern_scan.py src > build/audit_pattern_scan.txt
	@echo "pattern scan hints: build/audit_pattern_scan.txt"

clean:
	rm -rf build
