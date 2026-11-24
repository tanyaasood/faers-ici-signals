-- 04_events.sql : group MedDRA Preferred Terms into immune-related AE (irAE) groups
CREATE OR REPLACE TABLE irae_map(pt VARCHAR, ae_group VARCHAR);
INSERT INTO irae_map VALUES
 ('myocarditis','Myocarditis'), ('immune-mediated myocarditis','Myocarditis'), ('autoimmune myocarditis','Myocarditis'),
 ('pneumonitis','Pneumonitis'), ('immune-mediated lung disease','Pneumonitis'), ('interstitial lung disease','Pneumonitis'),
 ('colitis','Colitis'), ('immune-mediated enterocolitis','Colitis'), ('autoimmune colitis','Colitis'), ('enterocolitis','Colitis'),
 ('hepatitis','Hepatitis'), ('immune-mediated hepatitis','Hepatitis'), ('autoimmune hepatitis','Hepatitis'),
 ('hypophysitis','Hypophysitis'), ('lymphocytic hypophysitis','Hypophysitis'), ('hypopituitarism','Hypophysitis'),
 ('hypothyroidism','Thyroid'), ('hyperthyroidism','Thyroid'), ('thyroiditis','Thyroid'), ('immune-mediated thyroiditis','Thyroid'), ('autoimmune thyroiditis','Thyroid'),
 ('type 1 diabetes mellitus','Type 1 diabetes'), ('fulminant type 1 diabetes mellitus','Type 1 diabetes'), ('diabetic ketoacidosis','Type 1 diabetes'),
 ('myasthenia gravis','Neuromuscular'), ('myositis','Neuromuscular'), ('immune-mediated myositis','Neuromuscular');

-- One row per case per irAE group (counts cases, not reaction rows)
CREATE OR REPLACE TABLE case_event AS
SELECT DISTINCT c.caseid, m.ae_group
FROM reac r
JOIN cases c ON r.primaryid = c.primaryid
JOIN irae_map m ON lower(trim(r.pt)) = m.pt;
