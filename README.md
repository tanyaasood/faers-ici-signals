# Immune Checkpoint Inhibitor Safety Signals in FDA FAERS

Disproportionality analysis (PRR, ROR, IC) of immune-related adverse events (irAEs) for immune checkpoint inhibitors in FDA spontaneous reports.

**Status:** full year 2025 (Q1–Q4), with an oncology-only sensitivity analysis. PS-only and HCP-only sensitivity analyses still to do.

## How to run

```
pip install -r requirements-pipeline.txt
# put the unzipped FDA ASCII .txt files in data/raw/ (rename to UPPERCASE, e.g. DEMO25Q4.TXT, DELETE25Q4.TXT)
python src/run_pipeline.py   # SQL: load -> dedup -> drug mapping -> irAE grouping -> 2x2 counts
python src/stats.py          # PRR, ROR, IC + signal flags -> data/processed/signals.csv
python src/stats.py onc      # same, oncology-only background -> data/processed/signals_onc.csv
```

## Dashboard

`app.py` is a Streamlit dashboard (signal heatmap, drug comparison forest plot, all-FAERS vs oncology-only robustness plot, full results table). It reads only `data/processed/signals.csv`, `signals_onc.csv` and `summary.json`, so it runs without the raw FDA files.

```
pip install -r requirements.txt
streamlit run app.py
```

To deploy: push the repo to GitHub, go to share.streamlit.io, choose the repo and set the main file to `app.py`.

## Cleaning log (2025 Q1–Q4)

| Step | Count |
| --- | --- |
| DEMO rows loaded (report versions) | 1,617,444 |
| Distinct caseids | 1,469,305 (148,139 rows were older versions of the same case) |
| Withdrawn caseids in DELETE files | 21,483 listed; 3,497 present in 2025 data and removed |
| Cases after dedup + deletions | 1,465,808 |
| DRUG rows / REAC rows | 7,801,018 / 5,657,830 |
| Cases with a suspect (PS/SS) checkpoint inhibitor | 34,642 |

## Methods

- Drugs: matched on `prod_ai` (fallback `drugname`), suspect role only (PS/SS). Opdualag (nivolumab + relatlimab) excluded. Cases with both nivolumab and ipilimumab labelled as the combination regimen.
- Events: MedDRA Preferred Terms grouped into 8 irAE groups (see `sql/04_events.sql`).
- Background: all other deduplicated cases in the quarter.
- Signal = all three agree: Evans (a >= 3, PRR >= 2, Yates chi2 >= 4), ROR lower 95% CI > 1 with a >= 3, IC025 > 0.
- Verified: pembrolizumab x myocarditis count re-derived with an independent query (a = 109) and ROR checked by hand (23.79).

## Results (2025, full year)

64 of 72 regimen x irAE pairs meet all three criteria. Positive controls:

| Expected (from labels/literature) | Recovered? |
| --- | --- |
| Hypophysitis strongest with ipilimumab-containing regimens | Yes: nivolumab + ipilimumab ROR 113 (95% CI 85-151), ipilimumab alone 128 (52-314) vs 19-34 for PD-1/PD-L1 monotherapy |
| Colitis strongest with ipilimumab-containing regimens | Yes: nivolumab + ipilimumab ROR 27.2 (23.8-31.1), ipilimumab alone 34.6 (22.0-54.5) vs 8.6-12.0 for PD-1/PD-L1 monotherapy |
| Pneumonitis signals for PD-1/PD-L1 drugs | Yes: all 6 PD-1/PD-L1 drugs signal (ROR 8.6-14.6) |
| Myocarditis strongest with nivolumab + ipilimumab | Directionally only: nivolumab + ipilimumab ROR 29.6 (24.1-36.3) vs pembrolizumab 28.9 (26.0-32.1); CIs overlap, so not distinguishable in one year |

Note: in the Q4-only pilot, pembrolizumab ranked above the combination for myocarditis. With a full year the order reversed but the difference is not significant, which is a useful example of why one quarter is too small.

## Sensitivity analysis: oncology-only background

The main analysis compares checkpoint inhibitor cases with every other FAERS report. Cancer patients differ from the average report, which inflates RORs (confounding by indication). As a check, the background was restricted to 219,378 cases with a cancer indication (MedDRA indication terms matching cancer, carcinoma, neoplasm, lymphoma, etc.), plus all checkpoint inhibitor cases.

- RORs fell roughly 3–6 fold (e.g. nivolumab + ipilimumab hypophysitis 113 to 19.8), as expected when the comparator is other cancer patients.
- 57 of 72 pairs still signal (64 in the main analysis). No new signals appeared.
- All 7 lost signals had small counts (4–7 cases), except durvalumab with type 1 diabetes (30 cases, ROR 1.87, CI lower bound 1.30): this still meets the ROR criterion but fails the PRR/IC thresholds.
- Ranking held: ipilimumab-containing regimens stay highest for hypophysitis (ROR 19.8–22.0 vs 3.1–5.8) and colitis (9.5–11.5 vs 2.8–4.4). All PD-1/PD-L1 drugs still signal for pneumonitis.
- Myocarditis: pembrolizumab (8.2, 7.3–9.2) and nivolumab + ipilimumab (7.4, 6.0–9.0) are again indistinguishable. The expected higher risk with the combination is not detectable in one year of spontaneous reports.

Conclusion: the main immune-related adverse event signals are robust to an oncology-only comparator; their magnitude in the all-FAERS analysis is substantially inflated by confounding by indication.

## Limitations

- One year only; small counts for avelumab (306 cases), ipilimumab monotherapy (186) and cemiplimab (626).
- 'other ICI combination' (383 cases) mixes several regimens and is not interpretable on its own.
- Disproportionality measures reporting imbalance, not incidence or causation; no exposure denominator.
- Confounding by indication remains even within cancer patients (e.g. tumour type, prior chemotherapy). The oncology filter uses keyword matching on indication terms, not a validated MedDRA query.
- Notoriety and stimulated reporting; duplicate reports may remain; free-text drug names.
