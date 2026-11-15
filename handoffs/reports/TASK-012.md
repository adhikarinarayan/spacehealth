# TASK-012 — Complete

Evaluation-only replay of all four checksum-verified NASA DONKI windows. All **24 window/check combinations pass**, covering 12 grouped episodes and 48 crew/onset checks. Parsed GOES episodes match the supplied survey exactly. No frozen configuration, simulator, detector, source data or holdout results were changed; no holdout rerun, tuning or commits.

Outputs: model/reports/donki_replay/summary.md, results.json and four timeline PNGs. EXPERIMENT_LOG.md appended.

All crew act at the exact first retained onset sample. Every retained sample through warning and procedure hold is probed; May 2024's overlapping onset renews the active warning. All alarms clear under the unchanged TASK-005 rule. Radiation act card is first and survives the routine cap. Independent daily/cumulative integration agrees within 1e-6 mSv, with 19.5 mSv extra per window and explicit missing-sample/partial-coverage checks.

No rate-only acts occur outside warning plus procedure hold. Outside those intervals, provisional rate watch sample/day costs per crew: 2017-09 **21/2**; 2021-10 **135/4**; 2024-05 **0/0**; 2024-10 **53/4**. These are sample counts and distinct days, not clinical false-alert estimates.

Read-only adapter compatibility: load_events pins its checksum manifest key to the 2017 file. The evaluator takes each actual filename's digest from research/checksums.sha256 and provides a temporary alias manifest to the existing adapter. The adapter hashes and verifies the actual window bytes; a tampering test verifies rejection. No shared adapter/checksum edits.

Validation: focused replay tests **5 passed**; replay CLI passed and produced all artifacts; full model suite **151 passed**. Frozen config SHA256 remains `03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`; canonical-release manifest stability and science-scope verification pass in the full suite.

Real NASA DONKI SEP onset timing (observed near Earth); dose and Mars-transit mapping are simulation assumptions. NASA supplies timing, not crew dose or Mars observations.
