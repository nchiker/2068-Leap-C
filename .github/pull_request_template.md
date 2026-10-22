## What and why

<!-- What this changes, and the problem or issue it addresses (Fixes #...). -->

## Checks

- [ ] `make check` passes (budgets, platform deltas, RAM layout, documentation examples)
- [ ] `make repro` passes (two clean builds, identical hashes)
- [ ] Tests that fail without the change are added (or: no behaviour changes)
- [ ] For ROM code: `make budget` before and after, and the emulator suites run (`make test-fast`, or `make test` and `make fuse`); say which
- [ ] Documents updated (`spec.md`, `docs/`) where behaviour changes

## ROM images

<!-- If the images change: the new SHA-256 of build/leapc_home.bin and build/leapc_exrom.bin, and the free bytes from make budget. -->
