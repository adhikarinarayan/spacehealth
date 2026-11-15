# DONKI radiation robustness replay

real NASA DONKI SEP onset timing (observed near Earth); dose and Mars-transit mapping are simulation assumptions.

| Window | UTC onsets | Act samples (all crew) | Immediate | Renewal/hold | Clear | Dose | No outside rate act | Card | Warning / act hours | Extra mSv |
|---|---|---|---|---|---|---|---|---|---|---|
| 2017-09 | 2017-09-05T00:30:00Z, 2017-09-06T23:45:00Z, 2017-09-10T16:25:00Z | D60 0.5000h, D61 23.7500h, D65 16.4167h | PASS | PASS | PASS | PASS | PASS | PASS | 78.000 / 175.083 | 19.500000000 |
| 2021-10 | 2021-10-28T16:35:00Z, 2021-11-03T20:55:00Z | D60 16.5833h, D66 20.9167h | PASS | PASS | PASS | PASS | PASS | PASS | 52.000 / 106.500 | 19.500000000 |
| 2024-05 | 2024-05-10T13:35:00Z, 2024-05-11T02:10:00Z, 2024-05-13T14:00:00Z, 2024-06-08T02:25:00Z | D60 13.5833h, D61 2.1667h, D63 14.0000h, D89 2.4167h | PASS | PASS | PASS | PASS | PASS | PASS | 90.583 / 200.000 | 19.500000000 |
| 2024-10 | 2024-10-09T03:50:00Z, 2024-10-26T18:05:00Z, 2024-11-21T18:45:00Z | D60 3.8333h, D77 18.0833h, D103 18.7500h | PASS | PASS | PASS | PASS | PASS | PASS | 78.000 / 175.333 | 19.500000000 |

- All onsets flag immediately for all crew. Every retained sample throughout warning and hold is probed. May 2024 renews an already-active warning; orange plot shading includes procedure hold.
- Dose is independently integrated daily and cumulatively, including missing-sample coverage. The assumed 19.5 mSv per window is split equally among episodes; NASA supplies timing only.
- Outside warning plus procedure hold, provisional rate watches per crew (samples / distinct days): 2017-09: 21 / 2; 2021-10: 135 / 4; 2024-05: 0 / 0; 2024-10: 53 / 4. Survey differences: [].

Checksum adapter note: a temporary manifest aliases each original research/checksums.sha256 source digest to the read-only adapter’s fixed 2017 key; actual source bytes are still verified. Source data and original checksum manifests remain unchanged.
