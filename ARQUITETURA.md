# Arquitetura e Camadas do ETL

## Visão Geral

Este projeto segue uma arquitetura de **4 camadas** bem definidas, cada uma com responsabilidades específicas. Essa separação é fundamental para manutenibilidade, escalabilidade e conformidade com boas práticas de engenharia de dados.

## 🔄 As 4 Camadas

### 1. RAW (Camada de Ingestão)
**Localização:** Schema `raw`  
**Conteúdo:** Tabelas  
**Propósito:** Armazenar dados em seu estado original

- Dados ingeridos diretamente da fonte (CSV, API, banco externo)
- Nenhuma transformação aplicada
- Serve como **fonte de verdade histórica** para auditoria
- Permite rastrear mudanças e corrigir erros nas transformações

**Exemplo:**
```sql
SELECT * FROM raw.saude_municipios;
-- Contém "sao paulo", NULL, dados duplicados, tipos mistos
```

---

### 2. STAGING (Camada de Preparação)
**Localização:** Schema `staging`  
**Conteúdo:** Tabelas  
**Propósito:** Limpar, validar e normalizar dados

**Transformações aplicadas:**
- Capitalização: `"sao paulo"` → `"SAO PAULO"`
- Tratamento de nulos e valores inválidos
- Validação de ranges (ex: cobertura vacinal entre 0-100%)
- Conversão de tipos de dados
- Remoção de duplicatas
- Validação de integridade referencial

**Exemplo:**
```sql
SELECT * FROM staging.saude_municipios;
-- Dados limpos, normalizados e validados
```

---

### 3. DM (Data Mart)
**Localização:** Schema `dm`  
**Conteúdo:** Tabelas de fatos e dimensões  
**Propósito:** Fornecer dados prontos para análise

**Enhancements realizados:**
- Cálculos derivados (taxas, índices, taxas de incidência/mortalidade)
- Classificações (ex: "Excelente", "Bom", "Crítico")
- Chaves primárias e índices para performance
- Agregações pré-calculadas quando necessário

**Estrutura:**
- `saude_municipios` - Tabela de fatos principal
- Índices em colunas frequentemente consultadas (MUNICIPIO, UF, REGIAO)
- Primary key numérica (`ID_MUNICIPIO`) para relacionamentos

**Exemplo:**
```sql
SELECT ID_MUNICIPIO, MUNICIPIO, TAXA_INCIDENCIA_COVID, 
       TAXA_MORTALIDADE_COVID, CLASSIFICACAO_VACINACAO
FROM dm.saude_municipios
WHERE REGIAO = 'SUDESTE';
```

---

### 4. ANALYTICS (Camada de Visualização)
**Localização:** Schema `analytics`  
**Conteúdo:** Views  
**Propósito:** Fornecer perspectivas específicas para BI e relatórios

Esta é a camada **mais importante para quem usa os dados**:

#### Views disponíveis:

**a) `vw_resumo_regiao`**
- Agrega indicadores por região geográfica
- Uso: Dashboards regionais, comparativos entre regiões
- Colunas: Região, quantidade de municípios, população, casos, óbitos, cobertura vacinal média

**b) `vw_ranking_vacinacao`**
- Ranking ordenado por taxa de cobertura vacinal
- Uso: Identificar boas práticas e deficiências
- Colunas: Ranking, Municipio, UF, Taxa, Classificação

**c) `vw_analise_risco_covid`**
- Classifica municípios por nível de risco
- Uso: Priorização de ações de saúde pública
- Colunas: Município, indicadores de risco, classificações

**d) `vw_dashboard_estado`**
- Consolidação por estado
- Uso: Visão estratégica estadual
- Colunas: Estado, população, casos, cobertura, percentuais

**e) `vw_cidades_alerta`**
- Municípios que requerem atenção
- Uso: Alertas e monitoramento
- Colunas: Município, status de alerta, indicadores críticos

---

## 🎯 Por Que 4 Camadas?

| Camada | Responsabilidade | Quem Usa | Modificação |
|--------|------------------|----------|-------------|
| **RAW** | Preservar original | Auditoria, Data Stewards | Nunca (append-only) |
| **STAGING** | Validar e limpar | Engenheiros de dados | Frequente |
| **DM** | Enriquecer e otimizar | Engenheiros de dados, Analistas | Quando há novos cálculos |
| **ANALYTICS** | Expor perspectivas | Analistas, BI, Dashboards | Quando há novos insights |

---

## 🔧 Executando em Sequência

Cada camada depende da anterior:

```
01_create_schemas.sql           ← Cria os 4 schemas
    ↓
02_create_raw_tables.sql        ← Define tabelas RAW
    ↓
03_staging_transformations.sql  ← Carrega e transforma para STAGING
    ↓
04_dm_transformations.sql       ← Enriquece para DM
    ↓
05_dm_optimization.sql          ← Adiciona otimizações (PK, índices, comentários)
    ↓
06_analytics_views.sql          ← Cria views finais para análise
```

---

## 💡 Benefícios Desta Arquitetura

✅ **Separação de Responsabilidades**: Cada camada tem um propósito claro  
✅ **Rastreabilidade**: Posso auditar erros até a camada RAW  
✅ **Manutenibilidade**: Mudar uma view não afeta a tabela DM  
✅ **Performance**: Índices no DM, views otimizadas  
✅ **Escalabilidade**: Fácil adicionar novas views ou transformações  
✅ **Segurança**: Controle granular de permissões por schema  

---

## 📊 Exemplo Prático: Uma Consulta Completa

Rastrear uma métrica da origem até a visualização:

```sql
-- 1. Origem (RAW)
SELECT municipio, casos_covid_2023, populacao 
FROM raw.saude_municipios 
WHERE municipio = 'São Paulo';

-- 2. Validado (STAGING)
SELECT MUNICIPIO, CASOS_COVID_2023, POPULACAO 
FROM staging.saude_municipios 
WHERE MUNICIPIO = 'SAO PAULO';

-- 3. Enriquecido (DM)
SELECT MUNICIPIO, CASOS_COVID_2023, TAXA_INCIDENCIA_COVID
FROM dm.saude_municipios 
WHERE MUNICIPIO = 'SAO PAULO';

-- 4. Pronto para Análise (ANALYTICS)
SELECT MUNICIPIO, UF, TAXA_INCIDENCIA_COVID, NIVEL_RISCO_INCIDENCIA
FROM analytics.vw_analise_risco_covid
WHERE MUNICIPIO = 'SAO PAULO';
```

Cada camada adiciona valor e segurança ao pipeline.

---

## 📝 Conclusão

A separação em 4 camadas não é apenas uma boa prática — é essencial para construir sistemas de dados **confiáveis, escaláveis e auditáveis**. Este projeto demonstra essa arquitetura em um contexto real e pragmático.
