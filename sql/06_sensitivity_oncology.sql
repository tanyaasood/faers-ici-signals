-- 06_sensitivity_oncology.sql : oncology-only background
-- Main analysis compares ICI cases with ALL other FAERS cases. Cancer patients differ from the
-- average FAERS report, so here the universe is restricted to cases with a cancer indication
-- (plus every ICI case, so no ICI case is lost if its indication field is blank).

CREATE OR REPLACE TABLE onc_cases AS
SELECT DISTINCT c.caseid
FROM indi i
JOIN cases c ON i.primaryid = c.primaryid
WHERE regexp_matches(lower(i.indi_pt),
  'cancer|carcinoma|neoplasm|tumour|tumor|melanoma|lymphoma|leukaemia|leukemia|myeloma|sarcoma|glioma|glioblastoma|mesothelioma|blastoma|metasta|malignan')
UNION
SELECT caseid FROM case_regimen;

CREATE OR REPLACE TABLE counts_onc AS
WITH N  AS (SELECT count(*) AS n FROM onc_cases),
     ev_o AS (SELECT e.* FROM case_event e JOIN onc_cases USING (caseid)),
     dr AS (SELECT regimen,  count(DISTINCT caseid) AS n_drug  FROM case_regimen GROUP BY 1),
     ev AS (SELECT ae_group, count(DISTINCT caseid) AS n_event FROM ev_o GROUP BY 1),
     grid AS (SELECT regimen, ae_group FROM dr CROSS JOIN ev),
     ab AS (SELECT r.regimen, e.ae_group, count(DISTINCT r.caseid) AS a
            FROM case_regimen r JOIN ev_o e USING (caseid) GROUP BY 1, 2)
SELECT g.regimen, g.ae_group,
       coalesce(ab.a, 0)                                AS a,
       dr.n_drug - coalesce(ab.a, 0)                    AS b,
       ev.n_event - coalesce(ab.a, 0)                   AS c,
       N.n - dr.n_drug - ev.n_event + coalesce(ab.a, 0) AS d
FROM grid g
JOIN dr USING (regimen) JOIN ev USING (ae_group) CROSS JOIN N
LEFT JOIN ab USING (regimen, ae_group);

COPY counts_onc TO 'data/processed/counts_onc.parquet' (FORMAT parquet);
