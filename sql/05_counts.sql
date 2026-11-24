-- 05_counts.sql : 2x2 table counts for every regimen x irAE group pair
-- Background = every other deduplicated case in the database (full-database comparator).
CREATE OR REPLACE TABLE counts AS
WITH N  AS (SELECT count(*) AS n FROM cases),
     dr AS (SELECT regimen,  count(DISTINCT caseid) AS n_drug  FROM case_regimen GROUP BY 1),
     ev AS (SELECT ae_group, count(DISTINCT caseid) AS n_event FROM case_event   GROUP BY 1),
     grid AS (SELECT regimen, ae_group FROM dr CROSS JOIN ev),
     ab AS (SELECT r.regimen, e.ae_group, count(DISTINCT r.caseid) AS a
            FROM case_regimen r JOIN case_event e USING (caseid) GROUP BY 1, 2)
SELECT g.regimen, g.ae_group,
       coalesce(ab.a, 0)                                AS a,
       dr.n_drug - coalesce(ab.a, 0)                    AS b,
       ev.n_event - coalesce(ab.a, 0)                   AS c,
       N.n - dr.n_drug - ev.n_event + coalesce(ab.a, 0) AS d
FROM grid g
JOIN dr USING (regimen) JOIN ev USING (ae_group) CROSS JOIN N
LEFT JOIN ab USING (regimen, ae_group);

COPY counts TO 'data/processed/counts.parquet' (FORMAT parquet);
