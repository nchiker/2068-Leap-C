# 2068-Leap-C build (project_plan.md section 3 onwards: Phase 1 M1.1-M1.3, Phases 2-6).
#   make / make build   production images in build/, test images (-DLEAPC_TEST) in build/test/
#   make check          strict assembly (build), budgets, platform delta check, test-image check,
#                       RAM layout guard (static census of the RAM the ROMs reference, with negative
#                       controls)
#   make budget         per-component budget table and ROM map
#   make inventory      every HOME routine, table and gap with its referrers (docs/HOME_ROM_INVENTORY.md)
#   make test           ZEsarUX tests on the images (boot, lexer, declarations, executable C programs:
#                       expressions, statements, preprocessor, the library, runtime errors, BREAK,
#                       soak; helper, library, ISR, lexer and spike-workload measurements; memory
#                       layout, regions, stack, heap, banking invariants; the shell; the compile/run
#                       workflow: typed programs, the corpus through RUN, diagnostics, reports) and
#                       the canary, as tasks on a pool of emulators; needs ~/ts2068-debug, ZEsarUX 13.0
#   make canary         the RAM canary and banking invariants over the whole corpus (4 emulators)
#   make capacity       the measured capacity table (build/capacity.json, docs/milestones/M4.md)
#   make repro          two clean builds must give identical image hashes
#   make audit          z80-skills pattern scan of src/ (hints for the manual audit, not a gate)
.PHONY: all build prod testimg check budget inventory test canary capacity repro audit clean

ASM := tools/sjasm_strict.sh
SKILLS ?= $(HOME)/z80-skills/skills

all: build

build: prod testimg

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

check: build
	python3 tools/budget.py --check --json build/budget.json
	python3 tools/check_platform.py
	python3 tools/check_test_image.py
	python3 tools/check_ram_layout.py
	python3 tools/check_ram_layout.py --negative

budget: prod
	python3 tools/budget.py

inventory: prod
	python3 tools/rom_inventory.py

test: build
	python3 tools/run_tests.py

canary: build
	python3 tools/canary.py

capacity: build
	python3 tools/capacity.py

repro:
	tools/check_repro.sh

audit:
	mkdir -p build
	python3 $(SKILLS)/audit-z80/scripts/z80_pattern_scan.py src > build/audit_pattern_scan.txt
	@echo "pattern scan hints: build/audit_pattern_scan.txt"

clean:
	rm -rf build
