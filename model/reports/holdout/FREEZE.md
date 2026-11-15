# V1 freeze — recorded before holdout

UTC: 2026-11-15T18:35:28.540472+00:00

Config: model/configs/frozen_v1.yaml

SHA256: `9662bf1d498a9a729daf84c2dc73c92fcc7c0cd1943764ceaf886251b5289492`

M3 fixed EWMA lambda 0.2, control sigma 3; M5 info-only, fixed stage-2 parameters. Baseline/sleep/radiation and structured simulator inputs captured in config. 143 development tests passed. No holdout case had been run at this freeze. Exact code/data hashes and package versions: FREEZE.json. Release example preselected as seed 1000, Gaussian noise, effect scale 0.8.

The runner refuses changed config/code/data. STARTED prevents a second run; COMPLETE reuses cached artifacts and verifies their hashes. Any bug repair after results requires an explicitly labelled holdout-2 preserving this run.
