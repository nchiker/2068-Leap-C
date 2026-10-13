# 2068-Leap C --- Pre-Specification Architecture Investigation Plan

## 1. Purpose

This document defines the investigation that must be completed before
writing the final `spec.md` and implementation `project plan.md` for
2068-Leap C.

The investigation exists because the most important architectural
decisions for C should be based on measurements rather than assumptions
inherited from 2068-Leap BASIC, Pascal, Forth, Small-C, or modern
desktop C implementations.

The primary question is:

> Should normal 2068-Leap C compile to Leap bytecode, native Z80 machine
> code, or a deliberately hybrid execution model?

The investigation must also establish the practical language scope,
compiler/runtime memory budget, program RAM budget, calling convention
requirements, library strategy, platform ABI requirements, and
development-environment requirements needed for the final project
specification.

This phase does **not** build the production C compiler.

## 2. Mandatory Context

The investigation assumes:

-   Original Timex Sinclair 2068 target.
-   Z80A-compatible CPU.
-   48 KB RAM.
-   Replacement 24 KB HOME ROM architecture.
-   TS2068 HOME/EXROM banking facilities.
-   2068-Leap V2 as the primary platform-services reference.
-   No RAM expansion required for the base C system.
-   Existing Leap graphics, sound, input, storage, editor, banking,
    package, and debugging work should be reused where appropriate.
-   C should be capable of becoming a practical systems/programming
    language for Leap, not merely a demonstration compiler.

The investigation must not assume that the BASIC V2 VM is the correct
execution engine for C.

## 3. Required Final Deliverables

The investigation is complete only when it produces enough evidence to
write the actual C specification and project plan.

Required outputs:

1.  `docs/C_ARCHITECTURE_BASELINE.md`
2.  `docs/C_LANGUAGE_SCOPE_STUDY.md`
3.  `docs/C_IR_AND_BACKEND_SPIKE.md`
4.  `docs/C_BACKEND_BENCHMARK_RESULTS.md`
5.  `docs/C_MEMORY_BUDGET.md`
6.  `docs/C_CALLING_CONVENTION_STUDY.md`
7.  `docs/C_LIBRARY_AND_PLATFORM_ABI_STUDY.md`
8.  `docs/C_DEVELOPMENT_ENVIRONMENT_STUDY.md`
9.  `docs/C_ARCHITECTURE_DECISION.md`
10. A final checklist explicitly stating that sufficient information
    exists to write:
    -   `spec.md`
    -   `project plan.md`

The final architecture decision must cite measured results from the
investigation.

## 4. Questions the Investigation Must Answer

Before the production specification is written, answer all of the
following.

### Execution architecture

-   Bytecode, native Z80, or hybrid?
-   If bytecode, can the existing V2 VM be reused directly?
-   If not, what C-oriented VM extensions are needed?
-   If native, how large is the minimum useful native-code backend?
-   Can expensive operations use shared ROM helpers?
-   Does native code consume too much application RAM?
-   Is hybrid execution worth its added compiler/runtime complexity?
-   Should native code be the default with optional bytecode, or vice
    versa?
-   Is there value in per-function native/bytecode selection?

### Language

-   What historical/standard C dialect should define the language?
-   Which C89-style facilities are essential?
-   Which features should be omitted, deferred, or implemented as
    extensions?
-   What are the exact sizes of `char`, `short`, `int`, `long`, and
    pointers?
-   How are signed and unsigned arithmetic handled?
-   Are function pointers practical?
-   Are `struct`, `union`, `enum`, `typedef`, `static`, `extern`,
    `const`, and `volatile` in Release 1?
-   What preprocessor subset is practical?
-   Is floating point resident, optional, or omitted initially?

### Runtime

-   Calling convention?
-   Parameter passing?
-   Return values?
-   Local-variable layout?
-   Recursion?
-   Stack layout?
-   Heap layout?
-   `malloc`/`free`?
-   Stack/heap collision detection?
-   Function-pointer representation?
-   Far/banked calls if packages require them?

### Compiler

-   Can the compiler live primarily in ROM?
-   How much RAM does parsing/code generation require?
-   Can compiler workspace be reclaimed for runtime use?
-   Is a language-neutral intermediate representation worthwhile?
-   How large are the bytecode and native backends?
-   What optimization level is realistic on-machine?

### Platform

-   Which Leap V2 services can C call directly?
-   What language-neutral platform ABI should be frozen?
-   Can C produce Leap packages/extensions?
-   Can C libraries be consumed by BASIC, Pascal, or Forth?
-   How should banked/EXROM code be represented?

### Development environment

-   Can the Leap V2 full-screen editor be reused?
-   What source size is practical?
-   How are compiler diagnostics mapped back to source?
-   What save/load workflow is appropriate?
-   Can multi-file source be supported usefully on cassette?
-   Is an object/link stage useful or unnecessarily expensive?

## Phase 0 --- Freeze the Investigation Baselines

### Objectives

Establish the exact codebases and measurements being used.

### Tasks

Record:

-   Qualified 2068-Leap V2 revision.
-   HOME ROM usage.
-   EXROM usage.
-   Free ROM.
-   Platform-service sizes.
-   V2 VM size.
-   V2 compiler-related sizes.
-   V2 editor size/workspace.
-   Current RAM map.
-   Available program/application RAM.
-   Package ABI state.
-   Relevant arithmetic routines.
-   Relevant memory/banking services.

If Leap Pascal work has progressed far enough to contain tested
procedure-frame or VM improvements, record them separately. Do not make
the C investigation depend on unfinished Pascal code.

### Deliverable

`docs/C_ARCHITECTURE_BASELINE.md`

## Phase 1 --- Historical and Contemporary Z80 C Reference Study

### Objectives

Establish realistic expectations for C on a Z80.

### Reference categories

Study representative implementations such as:

-   Small-C family.
-   Hi-Tech C where useful documentation is available.
-   SDCC Z80.
-   z88dk/zsdcc/sccz80.
-   Other well-documented Z80 C implementations where relevant.

### Record

-   Type sizes.
-   Calling conventions.
-   Stack use.
-   Pointer representation.
-   Function-pointer behavior.
-   `struct` handling.
-   Library strategy.
-   Native code-generation patterns.
-   Optimization techniques.
-   Runtime helper strategy.
-   Compiler memory assumptions.
-   Generated-code size where measurable.

### Rule

These implementations are references and benchmark comparators, not
source donors.

### Deliverable

A section in `C_LANGUAGE_SCOPE_STUDY.md` and benchmark notes for later
phases.

## Phase 2 --- Proposed C Language Profile Study

### Objectives

Define the candidate Release-1 language before backend testing.

### Candidate scalar model

Investigate at minimum:

-   `char`: 8-bit.
-   `signed char`: 8-bit.
-   `unsigned char`: 8-bit.
-   `short`: likely 16-bit.
-   `int`: likely 16-bit.
-   `unsigned int`: 16-bit.
-   `long`: 32-bit.
-   `unsigned long`: 32-bit.
-   pointers: likely 16-bit within normal RAM address space.

Do not freeze these merely because they are conventional; confirm
implications.

### Candidate required features

Evaluate:

-   Functions.
-   Recursion.
-   Local/global variables.
-   Arrays.
-   Pointers.
-   Pointer arithmetic.
-   Function pointers.
-   `struct`.
-   `union`.
-   `enum`.
-   `typedef`.
-   `sizeof`.
-   Casts.
-   `if/else`.
-   `switch`.
-   `for`.
-   `while`.
-   `do/while`.
-   `break`.
-   `continue`.
-   `goto`.
-   Bitwise operators.
-   Logical operators.
-   Signed/unsigned comparison.
-   `static`.
-   `extern`.
-   `const`.
-   `volatile`.

### Preprocessor study

Evaluate cost/benefit of:

-   `#include`.
-   Object-like `#define`.
-   Function-like macros.
-   `#if`.
-   `#ifdef`.
-   `#ifndef`.
-   `#else`.
-   `#endif`.
-   Token concatenation.
-   Stringification.

The initial implementation should not automatically promise a complete
ANSI preprocessor.

### Deliverable

`docs/C_LANGUAGE_SCOPE_STUDY.md`

Classify every feature:

-   Required Release 1.
-   Desirable Release 1.
-   Optional/package/library.
-   Deferred.
-   Deliberately omitted.

## Phase 3 --- Define a Backend-Neutral Test IR

### Objectives

Test execution architectures without first implementing a C
lexer/parser.

### Requirements

Design the smallest temporary intermediate representation capable of
expressing:

-   Constants.
-   Local/global loads and stores.
-   Address calculation.
-   Pointer loads/stores.
-   Integer arithmetic.
-   Bitwise operations.
-   Comparisons.
-   Branches.
-   Function calls.
-   Returns.
-   Stack-frame creation.
-   Arrays.
-   Struct offsets.
-   Switch-like branching.
-   Runtime-helper calls.
-   Platform-service calls.

The IR is an investigation tool. It is not automatically part of the
final compiler architecture.

### Deliverable

Document in `docs/C_IR_AND_BACKEND_SPIKE.md`.

## Phase 4 --- Representative C Workload Suite

### Objectives

Create tests that expose meaningful differences between bytecode and
native execution.

### Required workloads

#### A. Arithmetic loop

Representative source:

    int sum(int n)
    {
        int s = 0;
        while (n) {
            s += n;
            --n;
        }
        return s;
    }

Measures arithmetic, locals, branches, and loop overhead.

#### B. Pointer walk

Representative source:

    void clear(char *p, unsigned n)
    {
        while (n--)
            *p++ = 0;
    }

Measures pointer arithmetic and indirect stores.

#### C. Memory copy

Representative source:

    void copy(char *d, const char *s, unsigned n)
    {
        while (n--)
            *d++ = *s++;
    }

Measures one of C's most important low-level workloads.

#### D. Array traversal

Use indexed 8-bit and 16-bit arrays.

#### E. Struct access

Exercise repeated fixed-offset fields.

#### F. Function calls

Exercise:

-   no parameters,
-   multiple parameters,
-   local variables,
-   8-bit return,
-   16-bit return,
-   32-bit return where supported.

#### G. Recursion

Use factorial and a deeper stack test.

#### H. Switch

Exercise small and larger `switch` cases.

#### I. Bit operations

Exercise shifts, masks, AND/OR/XOR, and byte extraction.

#### J. Graphics loop

Representative source:

    for (x = 0; x < 192; ++x)
        plot(x, x / 2);

Measures execution overhead when much work occurs in ROM services.

#### K. Mixed application

Create a small realistic TS2068 workload combining computation, input,
graphics, and function calls.

### Deliverable

The workload definitions belong in `C_IR_AND_BACKEND_SPIKE.md`.

## Phase 5 --- Bytecode Backend Spike

### Objectives

Determine how well C maps to compact Leap-style bytecode.

### Tasks

-   Map the test IR to the existing V2 VM where possible.
-   Identify missing operations.
-   Implement only the minimum experimental VM extensions needed for
    representative tests.
-   Measure extension ROM cost.
-   Generate bytecode for every workload.
-   Measure generated size.
-   Measure execution time/cycles.
-   Measure runtime stack use.
-   Measure temporary RAM.
-   Record platform-call overhead.

### Critical question

Determine whether C pointer-heavy code is disproportionately expensive
in the VM.

### Deliverable

Bytecode results in `docs/C_BACKEND_BENCHMARK_RESULTS.md`.

## Phase 6 --- Native Z80 Backend Spike

### Objectives

Determine the cost and benefit of compiling directly to Z80.

### Initial backend

The first backend should favor correctness and simplicity over
sophisticated optimization.

Support enough operations to compile the representative IR workloads.

### Investigate

-   Register allocation strategy.
-   IX/IY use.
-   Stack frame.
-   HL/DE/BC usage.
-   8-bit vs. 16-bit operations.
-   Pointer loads/stores.
-   Branches.
-   Calls/returns.
-   Struct offsets.
-   Switch strategy.

### Measure

-   Backend ROM/code size.
-   Generated program size.
-   Execution cycles/time.
-   Runtime stack.
-   Temporary RAM.
-   Complexity of code generation.

### Deliverable

Native results in `docs/C_BACKEND_BENCHMARK_RESULTS.md`.

## Phase 7 --- Native Z80 + ROM Helper Spike

### Objectives

Test whether shared ROM helpers provide the best balance.

### Candidate ROM helpers

Evaluate calls for expensive or uncommon operations such as:

-   16-bit multiply.
-   16-bit divide/modulus.
-   32-bit arithmetic.
-   Long shifts.
-   Switch dispatch.
-   Memory movement.
-   Numeric conversion.
-   Floating point if later supported.
-   Heap operations.

Cheap operations should remain inline where practical.

### Measure

Compare with pure/simple native output:

-   Program bytes saved.
-   Cycles added.
-   Helper ROM bytes required.
-   Compiler-backend simplification.

### Deliverable

Helper-assisted native results in `C_BACKEND_BENCHMARK_RESULTS.md`.

## Phase 8 --- Hybrid Architecture Spike

### Objectives

Determine whether mixing bytecode and native functions is worth
supporting.

### Candidate model

Test:

-   Normal functions as bytecode.
-   Selected functions as native Z80.
-   Calls in both directions.
-   Shared parameter/calling ABI if possible.

Representative hot function:

    __native void copy(...)

The syntax is illustrative only and must not be standardized during the
spike.

### Measure

-   Cross-mode call overhead.
-   Additional compiler ROM.
-   Additional runtime ROM.
-   Metadata requirements.
-   Program-size savings.
-   Performance recovered.
-   Debugging complexity.
-   Package/ABI implications.

### Decision rule

Hybrid should not be selected merely because it can be built.

It must recover a substantial portion of native performance while
retaining meaningful bytecode density advantages and acceptable
implementation complexity.

## Phase 9 --- External Compiler Sanity Comparison

### Objectives

Determine whether the experimental native backend produces plausible Z80
code.

### Compare representative programs with

-   SDCC Z80 output.
-   z88dk-supported Z80 compiler output where practical.

### Record

-   Generated bytes.
-   Broad instruction strategy.
-   Execution time/cycles where comparable.

Do not require the small on-machine Leap compiler to match mature
optimizing cross-compilers.

Use the comparison to identify obviously poor code generation.

### Deliverable

Comparison section in `C_BACKEND_BENCHMARK_RESULTS.md`.

## Phase 10 --- Calling Convention Study

### Objectives

Select or narrow the calling convention before final specification.

### Evaluate

-   Caller vs. callee cleanup.
-   Register parameters.
-   Stack parameters.
-   Return values.
-   8-bit return.
-   16-bit return.
-   32-bit return.
-   Struct return.
-   Function pointers.
-   Variadic functions if considered.
-   Recursion.
-   Local variables.
-   Frame pointer optionality.
-   Calls to ROM platform services.
-   Calls to package/EXROM services.
-   Native/bytecode interoperability if hybrid remains viable.

### Key concern

The convention should make ordinary C efficient without making package
interoperability unnecessarily difficult.

### Deliverable

`docs/C_CALLING_CONVENTION_STUDY.md`

## Phase 11 --- Compiler ROM/RAM Budget Study

### Objectives

Determine whether the desired compiler can coexist with the Leap
platform.

### Estimate or prototype costs for

-   Lexer.
-   Parser.
-   Symbol table.
-   Type system.
-   IR generation if used.
-   Bytecode backend.
-   Native backend.
-   Preprocessor.
-   Diagnostics.
-   Runtime helpers.
-   Editor integration.
-   Include/header handling.

### RAM study

Measure/estimate:

-   Source buffer.
-   Token/parser workspace.
-   Symbol table.
-   Type metadata.
-   Backend workspace.
-   Generated-program buffer.
-   Runtime globals.
-   Stack.
-   Heap.

Investigate overlaying compiler workspace with runtime stack/heap
because compilation and execution are mutually exclusive.

### Deliverable

`docs/C_MEMORY_BUDGET.md`

Include conservative and expected cases.

## Phase 12 --- Program Memory Model Study

### Objectives

Define how C sees the TS2068 address space.

### Resolve

-   Normal 16-bit pointers.
-   ROM addresses.
-   RAM addresses.
-   Video memory.
-   Volatile hardware access.
-   EXROM/banked memory.
-   Package code/data.
-   Function pointers into banked code.
-   Whether "far" pointers are needed.
-   Whether banked data is exposed directly or only through services.

### Principle

Do not contaminate ordinary C pointers with bank-switching complexity
unless required.

Prefer explicit platform APIs for unusual banked resources if that keeps
normal C efficient.

## Phase 13 --- Standard Library Scope Study

### Objectives

Determine what belongs in ROM, libraries, packages, or nowhere.

### Candidate small core

Evaluate:

-   `memcpy`.
-   `memmove`.
-   `memset`.
-   `memcmp`.
-   `strlen`.
-   `strcmp`.
-   `strcpy`/bounded alternatives.
-   Character classification.
-   Integer conversion.
-   `malloc`.
-   `free`.
-   Basic formatted output.

### Avoid assumption

Do not attempt to reproduce a desktop C standard library merely for
compatibility.

### Determine

-   Resident functions.
-   Linkable library functions.
-   Package functions.
-   Functions intentionally unsupported.

### Deliverable

Part of `docs/C_LIBRARY_AND_PLATFORM_ABI_STUDY.md`.

## Phase 14 --- Leap Platform API Study

### Objectives

Design what C should see of the existing platform.

### Candidate headers/modules

Conceptually:

    <leap/system.h>
    <leap/video.h>
    <leap/graphics.h>
    <leap/sprite.h>
    <leap/sound.h>
    <leap/input.h>
    <leap/storage.h>
    <leap/package.h>

Exact names are not fixed.

### Evaluate interfaces for

-   Screen/video.
-   Plot/line/circle/rect/fill.
-   Sprites.
-   UDGs.
-   ULAplus.
-   AY sound.
-   Keyboard.
-   Joystick.
-   Timing.
-   Storage.
-   Banking.
-   Package services.

### Requirement

C should support both:

1.  convenient Leap APIs, and
2.  direct hardware/memory access where safe and intentional.

### Deliverable

`docs/C_LIBRARY_AND_PLATFORM_ABI_STUDY.md`

## Phase 15 --- C as a Leap Systems Language Study

### Objectives

Determine whether C can practically build Leap extensions/packages.

### Prototype conceptually or experimentally

-   Compile a small C routine.
-   Package it.
-   Load it through the Leap package mechanism.
-   Call it.
-   Return values.
-   Pass pointers/buffers.
-   Unload safely.

### Investigate

Whether C-built services could be consumed by:

-   Leap BASIC.
-   Leap Pascal.
-   Leap Forth.
-   Leap C.

### Important question

Determine how much assembly is still required for a C-authored package.

### Decision target

A major success criterion for Leap C should be the ability to write
useful extensions without requiring most of the implementation to be
handwritten Z80 assembly.

## Phase 16 --- Development Environment Study

### Objectives

Determine how C development should work on the TS2068.

### Evaluate reuse of the V2 full-screen editor

Required considerations:

-   C punctuation entry.
-   Cursor/navigation.
-   Source scrolling.
-   Redraw/flicker behavior.
-   Error-line navigation.
-   Compile/run cycle.
-   Free-memory display.
-   Source save/load.
-   Include files.
-   Multiple translation units.

### Determine whether Release 1 should support

A. single-file programs only,

B. source includes,

C. separately compiled object modules,

D. a linker.

Do not add a linker merely because desktop C uses one.

Cassette workflow and 48K RAM may make a simpler source/library model
superior.

### Deliverable

`docs/C_DEVELOPMENT_ENVIRONMENT_STUDY.md`

## Phase 17 --- Backend Decision Matrix

### Objectives

Make the primary architectural decision using predefined criteria.

### Required comparison

  Metric                        Bytecode   Native   Native + ROM Helpers   Hybrid
  --------------------------- ---------- -------- ---------------------- --------
  Backend ROM                        TBD      TBD                    TBD      TBD
  Runtime/helper ROM                 TBD      TBD                    TBD      TBD
  Average program bytes              TBD      TBD                    TBD      TBD
  Arithmetic speed                   TBD      TBD                    TBD      TBD
  Pointer-loop speed                 TBD      TBD                    TBD      TBD
  Function-call speed                TBD      TBD                    TBD      TBD
  Graphics-app speed                 TBD      TBD                    TBD      TBD
  Runtime stack                      TBD      TBD                    TBD      TBD
  Compiler RAM                       TBD      TBD                    TBD      TBD
  Implementation complexity          TBD      TBD                    TBD      TBD
  Package suitability                TBD      TBD                    TBD      TBD
  Debugging complexity               TBD      TBD                    TBD      TBD

### Decision principles

#### Prefer bytecode if

-   program density is substantially better,
-   realistic applications are not materially slower,
-   native backend ROM cost is high,
-   and C remains useful for the intended workloads.

#### Prefer native if

-   pointer/memory/function-heavy C gains substantial speed,
-   program-size growth remains acceptable,
-   backend/runtime ROM fits comfortably,
-   and native output materially improves C's usefulness as a systems
    language.

#### Prefer native + ROM helpers if

-   it retains most native performance,
-   materially reduces generated program size or compiler complexity,
-   and shared helper ROM cost is reasonable.

#### Prefer hybrid only if

-   it delivers a clearly superior measured tradeoff,
-   cross-mode calls are inexpensive,
-   and compiler/runtime complexity remains justified.

### Deliverable

Decision matrix in `docs/C_ARCHITECTURE_DECISION.md`.

## Phase 18 --- Resource Feasibility Gate

### Objectives

Ensure the selected design is actually viable before specification.

The architecture must demonstrate a credible path to:

-   fitting the required development system within the ROM architecture,
-   retaining useful RAM for C source,
-   retaining useful RAM for compiled programs,
-   providing runtime stack and heap,
-   supporting representative applications,
-   and preserving required platform services.

If no candidate architecture meets these conditions, revise language
scope or backend design before proceeding.

Do not write the production spec around an architecture that has already
failed the resource model.

## Phase 19 --- Final Architecture Decision

### Required decisions

The final report must explicitly state:

1.  Default execution backend.
2.  Whether alternative backend support exists.
3.  Integer type sizes.
4.  Pointer model.
5.  Calling convention.
6.  Stack model.
7.  Heap model.
8.  Compiler workspace strategy.
9.  Preprocessor scope.
10. Release-1 language feature set.
11. Floating-point strategy.
12. Standard-library scope.
13. Leap platform API strategy.
14. Package-development strategy.
15. Editor/development workflow.
16. Source/module model.
17. HOME ROM budget.
18. EXROM/package budget.
19. RAM budget.
20. Performance expectations.

### Deliverable

`docs/C_ARCHITECTURE_DECISION.md`

This is the authoritative input to the production `spec.md`.

## Phase 20 --- Pre-Specification Review

### Objectives

Check that unresolved questions will not force the production
specification to guess.

### Checklist

Before writing `spec.md`, confirm:

-   Backend selected from measurements.
-   Calling convention selected.
-   Type sizes selected.
-   Pointer/banking model selected.
-   Core language scope selected.
-   Preprocessor scope selected.
-   Library scope selected.
-   Compiler ROM estimate exists.
-   Compiler RAM estimate exists.
-   Runtime RAM estimate exists.
-   Representative program-size measurements exist.
-   Representative speed measurements exist.
-   V2 platform reuse list exists.
-   Package strategy exists.
-   Editor workflow exists.
-   Storage/source workflow exists.
-   Major deferred features are identified.
-   Hardware constraints remain original 48K TS2068.

If any item materially affects architecture and remains unresolved, do
not invent an answer in the production specification. Resolve it first.

## Phase 21 --- Production Document Handoff

When all gates pass, use the investigation results to create:

### `spec.md`

The specification should define:

-   Hardware.
-   Language.
-   Compiler behavior.
-   Backend.
-   ABI.
-   Memory model.
-   Runtime.
-   Libraries.
-   Platform interfaces.
-   Development environment.
-   Storage.
-   Packages.
-   Errors.
-   Performance requirements.
-   Validation.
-   Release acceptance criteria.

### `project plan.md`

The implementation plan should then sequence:

-   foundation reuse,
-   compiler front end,
-   selected backend,
-   runtime,
-   libraries,
-   platform integration,
-   editor,
-   storage,
-   package support,
-   optimization,
-   testing,
-   real-hardware qualification,
-   documentation,
-   release.

The production project plan should not repeat architecture experiments
already settled by this investigation unless later measurements
invalidate an assumption.

## Investigation Guardrails

Throughout this pre-specification project:

-   Do not build the complete C compiler.
-   Do not choose bytecode merely because Leap V2 already has a VM.
-   Do not choose native merely because C is traditionally native
    compiled.
-   Do not choose hybrid merely because it appears flexible.
-   Do not assume 32-bit `int`.
-   Do not require expanded RAM.
-   Do not enlarge the hardware target to make the architecture fit.
-   Do not add desktop C facilities without evaluating their value on a
    48K TS2068.
-   Do not reproduce a large standard library merely for standards
    appearance.
-   Do not make the final specification until backend measurements
    exist.
-   Do not compare only synthetic arithmetic benchmarks; include
    pointer-heavy and platform-service-heavy workloads.
-   Do not treat cross-compiler output as the required standard for a
    small on-machine compiler.
-   Do not claim performance without repeatable measurements.
-   Do not make unfinished Pascal work a dependency of the
    investigation.
-   Reuse mature Leap V2 services where appropriate rather than
    reimplementing hardware support.
-   Preserve the V2 editor redraw/flicker safeguards if the editor is
    reused.
-   Use real TS2068 hardware for final confirmation of benchmark
    assumptions where practical.
-   Stop for user input only when a decision changes the hardware
    target, intended language character, major compatibility policy, or
    presents two genuinely comparable architectures whose tradeoff is
    subjective rather than measurable.

## Success Criterion

This investigation succeeds when the project can answer, with evidence
rather than intuition:

> What exactly is 2068-Leap C, how should it execute, what will it cost
> in ROM and RAM, how fast will representative programs run, how will
> programmers develop software with it, and how will it integrate with
> the rest of the 2068-Leap platform?

Only then should the final `spec.md` and implementation
`project plan.md` be written.
