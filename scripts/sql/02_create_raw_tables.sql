-- Tabela raw para dados brutos

DROP TABLE IF EXISTS raw.saude_municipios CASCADE;

CREATE TABLE raw.saude_municipios (
    municipio VARCHAR(100),
    uf VARCHAR(2),
    populacao INTEGER,
    casos_covid_2023 INTEGER,
    obitos_covid_2023 INTEGER,
    taxa_cobertura_vacina NUMERIC,
    pessoas_testadas INTEGER,
    data_atualizacao VARCHAR(20),
    regiao VARCHAR(50),
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
