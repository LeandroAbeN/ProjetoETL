-- Otimização e Constraints da Camada DM
-- Estabelece integridade referencial e chaves primárias para a tabela de fatos

ALTER TABLE dm.saude_municipios ADD PRIMARY KEY (ID_MUNICIPIO);

-- Comentários descritivos para melhorar documentação do schema
COMMENT ON TABLE dm.saude_municipios IS 'Tabela de fatos com dados de saúde, COVID-19 e vacinação em nível municipal. Contém indicadores calculados e classificações derivadas.';
COMMENT ON COLUMN dm.saude_municipios.TAXA_INCIDENCIA_COVID IS 'Taxa de incidência de COVID-19 por 100 mil habitantes';
COMMENT ON COLUMN dm.saude_municipios.TAXA_MORTALIDADE_COVID IS 'Taxa de mortalidade por COVID-19 (óbitos/casos * 100)';
COMMENT ON COLUMN dm.saude_municipios.PERCENTUAL_TESTADOS IS 'Percentual da população que foi testada para COVID-19';
COMMENT ON COLUMN dm.saude_municipios.CLASSIFICACAO_VACINACAO IS 'Classificação qualitativa da cobertura vacinal (Crítico, Regular, Bom, Excelente)';
