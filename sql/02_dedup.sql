-- 02_dedup.sql : FDA-recommended deduplication
-- Keep the latest version of each caseid (highest fda_dt, then highest primaryid),
-- then drop cases the FDA has withdrawn (DELETE files).
CREATE OR REPLACE TABLE cases AS
SELECT * EXCLUDE (rn) FROM (
  SELECT *, ROW_NUMBER() OVER (
           PARTITION BY caseid
           ORDER BY fda_dt DESC, CAST(primaryid AS BIGINT) DESC) AS rn
  FROM demo)
WHERE rn = 1
  AND caseid NOT IN (SELECT caseid FROM deleted);
