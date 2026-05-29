-- Camada Analytics: Views para visualização e BI
-- Estas views proporcionam diferentes perspectivas dos dados da camada DM
-- Dedicadas para consumo em ferramentas de análise e relatórios

-- View 1: Resumo por Região
-- Agrega indicadores-chave de COVID-19 e vacinação por região geográfica
DROP VIEW IF EXISTS analytics.vw_resumo_regiao CASCADE;

CREATE VIEW analytics.vw_resumo_regiao AS
SELECT
    REGIAO,
    COUNT(*) AS QUANTIDADE_MUNICIPIOS,
    SUM(POPULACAO) AS POPULACAO_TOTAL,
    SUM(CASOS_COVID_2023) AS TOTAL_CASOS_COVID,
    SUM(OBITOS_COVID_2023) AS TOTAL_OBITOS_COVID,
    ROUND(AVG(TAXA_COBERTURA_VACINA), 2) AS MEDIA_COBERTURA_VACINA,
    ROUND(AVG(TAXA_INCIDENCIA_COVID), 2) AS MEDIA_TAXA_INCIDENCIA
FROM dm.saude_municipios
GROUP BY REGIAO
ORDER BY POPULACAO_TOTAL DESC;


-- View 2: Ranking de Vacinação
-- Ordena municípios por taxa de cobertura vacinal com métricas complementares
DROP VIEW IF EXISTS analytics.vw_ranking_vacinacao CASCADE;

CREATE VIEW analytics.vw_ranking_vacinacao AS
SELECT
    ROW_NUMBER() OVER (ORDER BY TAXA_COBERTURA_VACINA DESC) AS RANK,
    MUNICIPIO,
    UF,
    REGIAO,
    TAXA_COBERTURA_VACINA,
    CLASSIFICACAO_VACINACAO,
    PERCENTUAL_TESTADOS
FROM dm.saude_municipios
ORDER BY TAXA_COBERTURA_VACINA DESC;


-- View 3: Análise de Risco COVID-19
-- Classifica municípios por nível de risco de incidência e mortalidade
DROP VIEW IF EXISTS analytics.vw_analise_risco_covid CASCADE;

CREATE VIEW analytics.vw_analise_risco_covid AS
SELECT
    MUNICIPIO,
    UF,
    REGIAO,
    POPULACAO,
    TAXA_INCIDENCIA_COVID,
    TAXA_MORTALIDADE_COVID,
    TAXA_COBERTURA_VACINA,
    CASE 
        WHEN TAXA_INCIDENCIA_COVID >= 1000 THEN 'ALTA'
        WHEN TAXA_INCIDENCIA_COVID >= 500 THEN 'MEDIA'
        ELSE 'BAIXA'
    END AS NIVEL_RISCO_INCIDENCIA,
    CASE 
        WHEN TAXA_MORTALIDADE_COVID >= 5 THEN 'CRITICO'
        WHEN TAXA_MORTALIDADE_COVID >= 2 THEN 'PREOCUPANTE'
        ELSE 'CONTROLADO'
    END AS NIVEL_RISCO_MORTALIDADE
FROM dm.saude_municipios
ORDER BY TAXA_INCIDENCIA_COVID DESC;


-- View 4: Dashboard por Estado
-- Consolida indicadores estratégicos em nível estadual para análise comparativa
DROP VIEW IF EXISTS analytics.vw_dashboard_estado CASCADE;

CREATE VIEW analytics.vw_dashboard_estado AS
SELECT
    UF,
    REGIAO,
    COUNT(*) AS MUNICIPIOS,
    SUM(POPULACAO) AS POPULACAO_TOTAL,
    ROUND(SUM(POPULACAO)::NUMERIC / SUM(SUM(POPULACAO)) OVER () * 100, 2) AS PERCENTUAL_POPULACAO_BRASIL,
    SUM(CASOS_COVID_2023) AS CASOS_TOTAIS,
    SUM(OBITOS_COVID_2023) AS OBITOS_TOTAIS,
    ROUND(SUM(OBITOS_COVID_2023)::NUMERIC / SUM(CASOS_COVID_2023) * 100, 2) AS TAXA_MORTALIDADE_ESTADO,
    ROUND(AVG(TAXA_COBERTURA_VACINA), 2) AS COBERTURA_VACINAL_MEDIA,
    ROUND(SUM(PESSOAS_TESTADAS)::NUMERIC / SUM(POPULACAO) * 100, 2) AS PERCENTUAL_TESTADOS_ESTADO
FROM dm.saude_municipios
GROUP BY UF, REGIAO
ORDER BY SUM(POPULACAO) DESC;


-- View 5: Cidades em Alerta
-- Identifica municípios que requerem atenção por indicadores críticos
DROP VIEW IF EXISTS analytics.vw_cidades_alerta CASCADE;

CREATE VIEW analytics.vw_cidades_alerta AS
SELECT
    MUNICIPIO,
    UF,
    REGIAO,
    POPULACAO,
    TAXA_COBERTURA_VACINA,
    TAXA_INCIDENCIA_COVID,
    TAXA_MORTALIDADE_COVID,
    CLASSIFICACAO_VACINACAO,
    CASE 
        WHEN TAXA_COBERTURA_VACINA < 70 AND TAXA_INCIDENCIA_COVID > 500 
            THEN 'CRITICO'
        WHEN TAXA_COBERTURA_VACINA < 75 
            THEN 'ALERTA'
        WHEN TAXA_MORTALIDADE_COVID > 3 
            THEN 'ALERTA'
        ELSE 'OK'
    END AS STATUS_ALERTA
FROM dm.saude_municipios
WHERE TAXA_COBERTURA_VACINA < 75 
   OR TAXA_MORTALIDADE_COVID > 3 
   OR (TAXA_COBERTURA_VACINA < 70 AND TAXA_INCIDENCIA_COVID > 500)
ORDER BY TAXA_COBERTURA_VACINA ASC;
