-- Transformação de RAW para STAGING

DROP TABLE IF EXISTS staging.saude_municipios CASCADE;

CREATE TABLE staging.saude_municipios AS
SELECT
    UPPER(TRIM(municipio)) AS MUNICIPIO,
    UPPER(TRIM(uf)) AS UF,
    CASE 
        WHEN populacao IS NULL OR populacao = 0 THEN NULL
        ELSE populacao 
    END AS POPULACAO,
    CASE 
        WHEN casos_covid_2023 IS NULL THEN 0
        ELSE casos_covid_2023 
    END AS CASOS_COVID_2023,
    CASE 
        WHEN obitos_covid_2023 IS NULL THEN 0
        ELSE obitos_covid_2023 
    END AS OBITOS_COVID_2023,
    CASE 
        WHEN taxa_cobertura_vacina IS NULL THEN 0
        WHEN taxa_cobertura_vacina > 100 THEN 100
        WHEN taxa_cobertura_vacina < 0 THEN 0
        ELSE ROUND(taxa_cobertura_vacina, 2)
    END AS TAXA_COBERTURA_VACINA,
    CASE 
        WHEN pessoas_testadas IS NULL THEN 0
        ELSE pessoas_testadas 
    END AS PESSOAS_TESTADAS,
    TO_DATE(data_atualizacao, 'YYYY-MM-DD') AS DATA_ATUALIZACAO,
    UPPER(TRIM(regiao)) AS REGIAO,
    CURRENT_TIMESTAMP AS DATA_TRANSFORMACAO
FROM raw.saude_municipios
WHERE municipio IS NOT NULL AND uf IS NOT NULL;

CREATE INDEX idx_staging_saude_municipio ON staging.saude_municipios(MUNICIPIO);
CREATE INDEX idx_staging_saude_uf ON staging.saude_municipios(UF);
CREATE INDEX idx_staging_saude_regiao ON staging.saude_municipios(REGIAO);
