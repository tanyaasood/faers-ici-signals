-- 01_load.sql : load raw FAERS/AEMS quarterly ASCII files ($-delimited)
-- quote='' because FAERS text fields are not quoted and contain stray " characters.
CREATE OR REPLACE TABLE demo AS SELECT * FROM read_csv('data/raw/DEMO*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);
CREATE OR REPLACE TABLE drug AS SELECT * FROM read_csv('data/raw/DRUG*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);
CREATE OR REPLACE TABLE reac AS SELECT * FROM read_csv('data/raw/REAC*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);
CREATE OR REPLACE TABLE outc AS SELECT * FROM read_csv('data/raw/OUTC*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);
CREATE OR REPLACE TABLE indi AS SELECT * FROM read_csv('data/raw/INDI*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);
CREATE OR REPLACE TABLE ther AS SELECT * FROM read_csv('data/raw/THER*.TXT', delim='$', header=true, quote='', escape='', all_varchar=true, union_by_name=true, filename=true, null_padding=true);

-- DELETE files: one caseid per line, no header (first line can be blank)
CREATE OR REPLACE TABLE deleted AS
SELECT DISTINCT trim(column0) AS caseid
FROM read_csv('data/raw/DELETE*.TXT', header=false, all_varchar=true, columns={'column0':'VARCHAR'})
WHERE trim(column0) <> '';
