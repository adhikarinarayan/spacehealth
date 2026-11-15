# Review — TASK-016 · Verdict: PASS — honest, modest real-data result

Reviewer: Claude · Sun 2026-11-15 ~14:15
- Re-run: tests 9 passed; `realdata.run` into scratch reproduces metrics.json exactly (timestamps excluded). Frozen config 03632b3d… and release manifest b3a49dd7… unchanged.
- Protocol fixed before results (protocol.json); first-listed symptom date rule disclosed; independent stdlib audit of one night matches to 2.8e-14 bpm.
- Results (F15): 13/21 within ±7 days (62%), 8/21 at/before onset (38%); controls 2.48 watch episodes / 100 nights.
- Claude context: chance of ≥1 watch episode in a 15-night window at the control rate ≈ 31% (≈ 18% for −7…0) → detection ≈ 2× chance. Real-world false-alert rate ≈ 3× simulator → simulator noise is optimistic; state in limits.
- Wording for public text: "sanity check, not a replication or clinical sensitivity estimate".
