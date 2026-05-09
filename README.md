# Projeto ETL - Portfolio

Um projeto prático de ETL desenvolvido com PostgreSQL, Python e Docker. O projeto implementa um pipeline de transformação de dados em 3 camadas (raw, staging e data mart) usando dados públicos de saúde brasileira como exemplo.

## Visão Geral

O projeto demonstra:
- Arquitetura em 3 camadas (raw, staging, dm)
- Transformação e limpeza de dados
- Views analíticas para BI
- Orquestração com Python
- Containerização com Docker
- Normalização e validação de dados  

## Arquitetura

```
Dados brutos (CSV) → RAW → STAGING → DM
                                      ↓
                            Views para análise
```

As três camadas:

**RAW**: Dados em seu estado original, nenhuma transformação. Serve como fonte de verdade e auditoria.

**STAGING**: Dados limpos e validados - normalização de strings, conversão de tipos, tratamento de nulos, validação de ranges.

**DM (Data Mart)**: Dados prontos para análise com cálculos derivados (taxas, índices, classificações) e índices para performance.

## Estrutura do Projeto

```
ProjetoETL/
├── README.md
├── QUICKSTART.md
├── docker-compose.yml
├── requirements.txt
├── .env.example
│
├── data/
│   ├── raw/
│   │   └── saude_municipios.csv
│   ├── staging/
│   └── dm/
│
└── scripts/
    ├── sql/
    │   ├── 01_create_schemas.sql
    │   ├── 02_create_raw_tables.sql
    │   ├── 03_staging_transformations.sql
    │   ├── 04_dm_transformations.sql
    │   └── 05_analytics_views.sql
    └── python/
        └── load_data.py
```

## Executando o Projeto

### Pré-requisitos

- Docker e Docker Compose
- PostgreSQL 15
- Python 3.8+
- psycopg2: `pip install psycopg2-binary`

### Com Docker (recomendado)

Inicie o PostgreSQL:
```bash
docker-compose up -d
```

Conecte ao banco:
```bash
docker exec -it etl_postgres psql -U etl_user -d etl_portfolio
```

Execute os scripts SQL em ordem:
```bash
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio < scripts/sql/01_create_schemas.sql
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio < scripts/sql/02_create_raw_tables.sql
```

Carregue os dados CSV:
```bash
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio -c "\COPY raw.saude_municipios(municipio,uf,populacao,casos_covid_2023,obitos_covid_2023,taxa_cobertura_vacina,pessoas_testadas,data_atualizacao,regiao) FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',')" < /workspaces/ProjetoETL/data/raw/saude_municipios.csv
```

Execute as transformações:
```bash
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio < scripts/sql/03_staging_transformations.sql
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio < scripts/sql/04_dm_transformations.sql
docker exec -i etl_postgres psql -U etl_user -d etl_portfolio < scripts/sql/05_analytics_views.sql
```

Para explorar os dados:
```sql
SELECT * FROM dm.vw_resumo_regiao;
SELECT * FROM dm.vw_ranking_vacinacao;
SELECT * FROM dm.vw_cidades_alerta;
SELECT * FROM dm.vw_dashboard_estado;
```

Ou acesse pgAdmin em http://localhost:5050 (admin@etl.local / admin123)

---

## 🔄 Fluxo de Transformação

### 1️⃣ RAW → STAGING

**Transformações aplicadas:**
```sql
-- Exemplo: Capitalização e limpeza
UPPER(TRIM(municipio))           -- "sao paulo" → "SAO PAULO"

-- Handel nulos
CASE WHEN populacao IS NULL OR populacao = 0 
  THEN NULL ELSE populacao END  -- Trata valores inválidos

-- Validação de range
CASE WHEN taxa_cobertura_vacina > 100 THEN 100 
  WHEN taxa_cobertura_vacina < 0 THEN 0 
  ELSE taxa_cobertura_vacina END -- Limita entre 0-100

-- Conversão de tipo
TO_DATE(data_atualizacao, 'YYYY-MM-DD') -- String → DATE
```

### 2️⃣ STAGING → DM

**Cálculos e métricas adicionadas:**
```sql
-- Taxa de incidência (por 100 mil habitantes)
ROUND(CAST(CASOS_COVID_2023 AS NUMERIC) / POPULACAO * 100000, 2)
→ 9.845 caso por 100 mil pessoas em SP

-- Taxa de mortalidade
ROUND(CAST(OBITOS_COVID_2023 AS NUMERIC) / CASOS_COVID_2023 * 100, 2)
→ 3.63% de óbitos/casos

-- Classificação (CASE para categoria)
CASE WHEN TAXA_COBERTURA_VACINA >= 90 THEN 'Excelente'
     WHEN TAXA_COBERTURA_VACINA >= 80 THEN 'Bom'
     ELSE 'Regular' END
```

---

## 📊 Views Analíticas (Prontas para BI)

### 1. `vw_resumo_regiao`
Resumo consolidado por região com comparativos:

```sql
SELECT * FROM dm.vw_resumo_regiao;
```

| REGIAO | QUANTIDADE_MUNICIPIOS | POPULACAO_TOTAL | MEDIA_COBERTURA_VACINA |
|--------|----------------------|-----------------|------------------------|
| SUDESTE | 4 | 22.447.400 | 87.53 |
| NORDESTE | 5 | 7.532.207 | 79.54 |
| SUL | 2 | 3.432.397 | 87.80 |

**Uso**: Dashboard regional, políticas públicas por região

---

### 2. `vw_ranking_vacinacao`
Cidades ordenadas pela cobertura vacinal:

```sql
SELECT * FROM dm.vw_ranking_vacinacao LIMIT 5;
```

| RANK | MUNICIPIO | TAXA_COBERTURA_VACINA | CLASSIFICACAO_VACINACAO |
|------|-----------|----------------------|------------------------|
| 1 | BRASILIA | 90.10 | Excelente |
| 2 | BELO HORIZONTE | 89.30 | Excelente |
| 3 | PORTO ALEGRE | 88.90 | Excelente |
| 4 | SAO PAULO | 87.50 | Bom |

**Uso**: Identificar líderes e gargalos em vacinação

---

### 3. `vw_analise_risco_covid`
Análise de risco com classificações:

```sql
SELECT * FROM dm.vw_analise_risco_covid 
WHERE NIVEL_RISCO_INCIDENCIA = 'ALTA';
```

**Uso**: Alertar sobre municipios em risco

---

### 4. `vw_dashboard_estado`
Dashboard consolidado por estado com KPIs:

```sql
SELECT * FROM dm.vw_dashboard_estado ORDER BY POPULACAO_TOTAL DESC;
```

**Colunas principais:**
- `TAXA_MORTALIDADE_ESTADO` - Óbitos / Casos (%)
- `COBERTURA_VACINAL_MEDIA` - Média de cobertura
- `PERCENTUAL_TESTADOS_ESTADO` - Pessoas testadas (%)

---

### 5. `vw_cidades_alerta`
Cidades que acionaram status de alerta:

```sql
SELECT * FROM dm.vw_cidades_alerta;
```

**Critérios de alerta:**
- ❌ Vacinação < 70% E Alta incidência → **CRÍTICO**
- ⚠️ Vacinação < 75% → **ALERTA**
- ⚠️ Taxa morte > 3% → **ALERTA**

---

## 📝 Exemplos de Queries Analíticas

### Qual região tem melhor cobertura vacinal?
```sql
SELECT REGIAO, ROUND(AVG(TAXA_COBERTURA_VACINA), 2) as media 
FROM dm.saude_municipios 
GROUP BY REGIAO 
ORDER BY media DESC; 
```

### Municípios com mais de 1% de incidência COVID?
```sql
SELECT MUNICIPIO, UF, TAXA_INCIDENCIA_COVID, CLASSIFICACAO_VACINACAO 
FROM dm.saude_municipios 
WHERE TAXA_INCIDENCIA_COVID > 1000 
ORDER BY TAXA_INCIDENCIA_COVID DESC;
```

### Taxa de mortalidade por estado vs cobertura vacinal
```sql
SELECT UF,  
       ROUND(AVG(TAXA_MORTALIDADE_COVID), 2) as taxa_morte, 
       ROUND(AVG(TAXA_COBERTURA_VACINA), 2) as cob_vacina 
FROM dm.saude_municipios 
GROUP BY UF 
ORDER BY taxa_morte DESC;
```

### Comparação: Cidades com ótima vacinação vs alta mortaldade
```sql
SELECT MUNICIPIO, POPULACAO, TAXA_COBERTURA_VACINA, TAXA_MORTALIDADE_COVID 
FROM dm.saude_municipios 
WHERE TAXA_COBERTURA_VACINA > 85 AND TAXA_MORTALIDADE_COVID > 3;
```

---

## 🔧 Customizações e Extensões

### Adicionar novo indicador no DM
1. Adicione a coluna na view em `04_dm_transformations.sql`
2. Crie um índice se for usada em filtros
3. Atualize as views analíticas

### Adicionar nova fonte de dados
1. Coloque o CSV em `data/raw/`
2. Crie uma tabela RAW correspondente
3. Implemente a lógica de transformação em STAGING
4. Agregue no DM com as respectivas métricas

### Conectar com BI (Power BI, Tableau, Metabase)
As views em `dm.*` estão prontas para conexão direta:
- **Connection String:**
  ```
  postgresql://etl_user:etl_password123@localhost:5432/etl_portfolio
  ```
- **Favor criar usuário read-only para produção**

---

## 💡 Melhores Práticas Aplicadas

| Prática | Implementação |
|---------|---------------|
| **Separação de responsabilidades** | 3 camadas com propósitos claros |
| **Idempotência** | Scripts com DROP IF EXISTS |
| **Documentação** | COMMENTS em tabelas e colunas |
| **Performance** | Índices nas colunas chave |
| **Rastreabilidade** | Colunas de data_carga e data_transformacao |
| **Validação de dados** | CASE/WHEN para limpar outliers |
| **Orquestração** | Script Python automático |
| **Versionamento** | Git + .gitignore |
| **Containerização** | Docker para reprodutibilidade |

---

## 📊 Dados no Projeto

**Fonte:** Dados de saúde pública brasileira (2023)  
**Período:** Dezembro 2023  
**Registros:** 15 municípios brasileiros  
**Campos:** População, casos COVID, óbitos, vacinação, testes, etc.

**Exemplos de dados:**
- São Paulo: 12.4M habitants, 87.5% cobertura vacinal
- Manaus: 1.8M habitants, 75.3% cobertura vacinal
- Brasília: 3.1M habitants, 90.1% cobertura vacinal (melhor)

---

## 🛑 Troubleshooting

### Erro: `connection refused` no psycopg2
**Solução:** Certifique-se que Docker está rodando: `docker-compose ps`

### Tabelas vazias após executar scripts
**Solução:** Os dados precisam ser carregados manualmente. Execute: 
```bash
\COPY raw.saude_municipios FROM 'data/raw/saude_municipios.csv' 
WITH (FORMAT csv, HEADER true, DELIMITER ',');
```

### Erro: `COPY ... FROM stdin` não funciona
**Solução:** Use `\COPY` (backslash) no psql em vez de `COPY`

### Port 5432 já está em uso
**Solução:** Mude a porta no `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Host:Container
```

---

## 📚 Arquivos Importantes

| Arquivo | Propósito |
|---------|-----------|
| `scripts/sql/01_create_schemas.sql` | Define as 3 camadas (raw, staging, dm) |
| `scripts/sql/02_create_raw_tables.sql` | Estrutura para dados brutos |
| `scripts/sql/03_staging_transformations.sql` | Limpeza e validação |
| `scripts/sql/04_dm_transformations.sql` | Cálculos e métricas |
| `scripts/sql/05_analytics_views.sql` | 5 views prontas para BI |
| `scripts/python/load_data.py` | Orquestrador automático |
| `docker-compose.yml` | PostgreSQL + pgAdmin containerizado |

---

## 🎯 O que este projeto demonstra para o portfólio

✅ **Conhecimento de ETL** - Engenharia de dados estruturada  
✅ **SQL Avançado** - Cálculos, views, otimização  
✅ **Modelagem de dados** - 3 camadas bem definidas  
✅ **Python** - Orquestração e automação  
✅ **Banco de dados** - PostgreSQL em produção  
✅ **Docker** - Containerização e DevOps  
✅ **BI** - Views prontas para ferramentas analíticas  
✅ **Documentação** - Projeto bem explicado e reprodutível  
✅ **Git** - Versionamento de código  
✅ **Boas práticas** - Código limpo, comentado, idempotente  

---

## 📞 Próximos Passos (Melhorias Futuras)

- [ ] Implementar incremental loading (apenas novos dados)
- [ ] Adicionar testes automatizados com pytest
- [ ] Criar CI/CD com GitHub Actions
- [ ] Adicionar data quality checks com Great Expectations
- [ ] Implementar erro handling mais robusto
- [ ] Adicionar logs estruturados (Serilog/Logger)
- [ ] Criar API REST para consumir os dados (FastAPI)
- [ ] Setup de monitoramento com Prometheus

---

## 📄 Licença

Este projeto é de código aberto para fins educacionais e de portfólio.

---

## 👤 Autor

Projeto criado como mini-portfólio de engenharia de dados.

**Tecnologias:** PostgreSQL | Python | SQL | Docker | ETL | Data Warehouse

---

**Última atualização:** 09/05/2026

---

## ⭐ Se este projeto foi útil, considere dar uma estrela! 🌟