"""Disproportionality statistics (PRR, ROR, IC) for every regimen x irAE pair.
Run after run_pipeline.py:
    python src/stats.py                      # main analysis (all-FAERS background)
    python src/stats.py onc                  # oncology-only background
"""
import sys
import numpy as np, pandas as pd

ANALYSIS = sys.argv[1] if len(sys.argv) > 1 else "main"
IN  = {"main": "data/processed/counts.parquet", "onc": "data/processed/counts_onc.parquet"}[ANALYSIS]
OUT = {"main": "data/processed/signals.csv",    "onc": "data/processed/signals_onc.csv"}[ANALYSIS]
from scipy.stats import chi2_contingency

df = pd.read_parquet(IN)
a, b, c, d = (df[k].astype(float) for k in "abcd")
N = a + b + c + d

with np.errstate(divide="ignore", invalid="ignore"):
    df["prr"] = (a / (a + b)) / (c / (c + d))
    df["ror"] = (a * d) / (b * c)
    se = np.sqrt(1/a + 1/b + 1/c + 1/d)
    df["ror_lo"] = np.exp(np.log(df.ror) - 1.96 * se)
    df["ror_hi"] = np.exp(np.log(df.ror) + 1.96 * se)

def yates_chi2(i, j, k, l):
    if min(i + j, k + l, i + k, j + l) == 0:
        return np.nan
    return chi2_contingency([[i, j], [k, l]], correction=True)[0]

df["chi2"] = [yates_chi2(*row) for row in zip(a, b, c, d)]

E = (a + b) * (a + c) / N
df["ic"] = np.log2((a + 0.5) / (E + 0.5))
df["ic025"] = df.ic - 3.3 * (a + 0.5) ** -0.5 - 2 * (a + 0.5) ** -1.5  # Noren et al. approximation

df["sig_prr"] = (a >= 3) & (df.prr >= 2) & (df.chi2 >= 4)
df["sig_ror"] = (a >= 3) & (df.ror_lo > 1)
df["sig_ic"] = df.ic025 > 0
df["signal"] = df.sig_prr & df.sig_ror & df.sig_ic

df = df.sort_values(["ae_group", "ror"], ascending=[True, False])
df["analysis"] = ANALYSIS
df.round(3).to_csv(OUT, index=False)

pd.set_option("display.width", 200)
cols = ["regimen", "ae_group", "a", "prr", "ror", "ror_lo", "ror_hi", "ic025", "signal"]
print(df[cols].round(2).to_string(index=False))
print(f"\nSignals (all three methods agree): {int(df.signal.sum())} of {len(df)} pairs")
