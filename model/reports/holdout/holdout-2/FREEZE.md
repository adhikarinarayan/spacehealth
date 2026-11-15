# Holdout-2 freeze — metadata-only repair

UTC: 2026-11-15T18:40:00.905934+00:00

SHA256: `03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`

First run preserved in parent directory. Its validated exports were written, but CLI metadata writing failed because inputSources was absent from the frozen loader. Fixed propagation and added a full dev-seed CLI regression; 144 tests pass. Same scientific parameters, seeds, distributions and release example. This run is explicitly holdout-2, not independent validation. Code/data hashes in FREEZE.json.
