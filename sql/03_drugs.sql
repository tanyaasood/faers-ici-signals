-- 03_drugs.sql : map immune checkpoint inhibitors and build one regimen per case
CREATE OR REPLACE TABLE ici_map(pattern VARCHAR, ingredient VARCHAR, class VARCHAR);
INSERT INTO ici_map VALUES
 ('%PEMBROLIZUMAB%','pembrolizumab','PD-1'), ('%KEYTRUDA%','pembrolizumab','PD-1'),
 ('%NIVOLUMAB%','nivolumab','PD-1'),         ('%OPDIVO%','nivolumab','PD-1'),
 ('%CEMIPLIMAB%','cemiplimab','PD-1'),       ('%LIBTAYO%','cemiplimab','PD-1'),
 ('%ATEZOLIZUMAB%','atezolizumab','PD-L1'),  ('%TECENTRIQ%','atezolizumab','PD-L1'),
 ('%DURVALUMAB%','durvalumab','PD-L1'),      ('%IMFINZI%','durvalumab','PD-L1'),
 ('%AVELUMAB%','avelumab','PD-L1'),          ('%BAVENCIO%','avelumab','PD-L1'),
 ('%IPILIMUMAB%','ipilimumab','CTLA-4'),     ('%YERVOY%','ipilimumab','CTLA-4');

-- Suspect ICIs per case (PS = primary suspect, SS = secondary suspect).
-- Opdualag (nivolumab + relatlimab) is excluded so it doesn't count as plain nivolumab.
CREATE OR REPLACE TABLE case_drug AS
SELECT DISTINCT c.caseid, m.ingredient, m.class
FROM drug d
JOIN cases c ON d.primaryid = c.primaryid
JOIN ici_map m
  ON upper(coalesce(nullif(trim(d.prod_ai),''), d.drugname)) LIKE m.pattern
WHERE d.role_cod IN ('PS','SS')
  AND upper(coalesce(d.prod_ai,'') || ' ' || coalesce(d.drugname,'')) NOT LIKE '%RELATLIMAB%'
  AND upper(coalesce(d.drugname,'')) NOT LIKE '%OPDUALAG%';

-- One regimen label per case. Nivo+ipi is its own regimen; other multi-ICI cases are rare and labelled 'other ICI combination'.
CREATE OR REPLACE TABLE case_regimen AS
WITH agg AS (
  SELECT caseid, list_sort(list(DISTINCT ingredient)) AS ings FROM case_drug GROUP BY caseid)
SELECT caseid,
  CASE WHEN len(ings) = 1 THEN ings[1]
       WHEN ings = ['ipilimumab','nivolumab'] THEN 'nivolumab + ipilimumab'
       ELSE 'other ICI combination' END AS regimen
FROM agg;
