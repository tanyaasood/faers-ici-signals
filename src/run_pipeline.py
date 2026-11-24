"""Run the SQL pipeline (load -> dedup -> drugs -> events -> counts) and print a cleaning log.
Run from the project root:  python src/run_pipeline.py
"""
import duckdb, pathlib, json

con = duckdb.connect("faers.duckdb")
for f in sorted(pathlib.Path("sql").glob("0*.sql")):
    print(f"running {f.name}")
    con.execute(f.read_text())

def q(sql):
    return con.execute(sql).fetchone()[0]

log = {
    "DEMO rows loaded (report versions)": q("SELECT count(*) FROM demo"),
    "Distinct caseids": q("SELECT count(DISTINCT caseid) FROM demo"),
    "Withdrawn caseids in DELETE file": q("SELECT count(*) FROM deleted"),
    "Cases after dedup + deletions": q("SELECT count(*) FROM cases"),
    "DRUG rows": q("SELECT count(*) FROM drug"),
    "REAC rows": q("SELECT count(*) FROM reac"),
    "Cases with a suspect ICI": q("SELECT count(*) FROM case_regimen"),
    "Cases with any irAE group": q("SELECT count(DISTINCT caseid) FROM case_event"),
}
print("\nCLEANING LOG")
for k, v in log.items():
    print(f"  {k:40s} {v:>10,}")

print("\nICI cases by regimen")
print(con.execute("SELECT regimen, count(*) n FROM case_regimen GROUP BY 1 ORDER BY 2 DESC").df().to_string(index=False))

# Small summary file for the dashboard
regimens = con.execute("SELECT regimen, count(*) n FROM case_regimen GROUP BY 1 ORDER BY 2 DESC").fetchall()
json.dump({"cleaning_log": log, "regimen_counts": dict(regimens)},
          open("data/processed/summary.json", "w"), indent=2)
print("wrote data/processed/summary.json")
