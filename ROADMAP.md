# Roadmap de Desenvolvimento - ProjetoETL

## 📋 Visão Geral
Este documento rastreia os próximos passos de codificação para melhorar a robustez e manutenibilidade do projeto ETL.

---

## 🔴 Fase 1: Correção Imediata ⚠️
**Status:** 🔄 Em Progresso  
**Objetivo:** Corrigir bugs críticos e implementar validações básicas

- [x] Corrigir typos e referências erradas em `load_data.py`
- [x] Adicionar validações de pré-requisitos (arquivos, schemas, tabelas)
- [x] Implementar logging com `logging` module
- [ ] Testar o script em ambiente Docker

**Arquivos afetados:**
- `scripts/python/load_data.py`

---

## 🔧 Fase 2: Melhorias
**Status:** 🔄 Em Progresso  
**Objetivo:** Aumentar confiabilidade e observabilidade

- [x] Adicionar script de validação de dados (count, null checks, ranges)
- [x] Criar script de rollback/reset do banco
- [ ] Implementar tratamento de idempotência (execução segura múltiplas vezes)
- [ ] Adicionar função de verificação de integridade das transformações

**Arquivos a criar:**
- [x] `scripts/python/validate_data.py`
- [x] `scripts/python/rollback_db.py`

---

## 💪 Fase 3: Robustez
**Status:** ⏳ Aguardando Fase 2  
**Objetivo:** Adicionar testes e monitoramento

- [ ] Adicionar testes unitários (pytest)
- [ ] Criar função de monitoramento de transformações
- [ ] Implementar versionamento de esquema (controle de mudanças)
- [ ] Adicionar tratamento de exceções customizadas

**Arquivos a criar:**
- `tests/test_load_data.py`
- `tests/test_transformations.py`
- `scripts/python/monitor_etl.py`

---

## 📚 Fase 4: Documentação
**Status:** ⏳ Aguardando Fase 3  
**Objetivo:** Melhorar experiência do usuário

- [ ] Documentar as views do Analytics (exemplos de queries)
- [ ] Criar guia de troubleshooting
- [ ] Adicionar exemplos de uso em Jupyter
- [ ] Criar script de exemplo de análises

**Arquivos a criar:**
- `docs/ANALYTICS_VIEWS.md`
- `docs/TROUBLESHOOTING.md`
- `notebooks/exemplo_analises.ipynb`

---

## ✅ Checklist de Execução

### Fase 1 - Checklist Detalhado
- [x] Corrigir linha 18: typo "Connectionect" → "Conectado"
- [x] Corrigir linha 91: schema 'dm' → 'analytics'
- [x] Corrigir linha 84: referência correta do arquivo SQL
- [x] Adicionar validação de existência do CSV
- [x] Adicionar validação de schemas/tabelas antes de inserir
- [x] Implementar logging estruturado com níveis (DEBUG, INFO, WARNING, ERROR)
- [x] Adicionar timestamps nos logs
- [x] Testar sem erros

---

## 📝 Notas de Progresso

### Sessão 1 (2026-06-15)
- ✅ Criado ROADMAP.md
- ✅ Atualizado .gitignore
- ✅ Corrigidos bugs em load_data.py
- ✅ Implementado logging
- ✅ Primeiro commit

### Sessão 2 (2026-06-19)
- ✅ Criado `validate_data.py` com validações:
  - Contagem de registros em cada etapa (raw → staging → analytics)
  - Verificação de valores nulos em colunas críticas
  - Validação de ranges (população, COVID, cobertura vacinal)
  - Validação de integridade referencial
  - Relatório resumido de qualidade
- ✅ Criado `rollback_db.py` com funcionalidades:
  - Menu interativo (listar status, tamanho, rollback parcial/completo)
  - Rollback com TRUNCATE (mais eficiente)
  - Proteção contra exclusão acidental (confirmação dupla)
  - Logging de todas operações

---

## 🚀 Como Executar Cada Fase

```bash
# Fase 1: Executar o script melhorado
python scripts/python/load_data.py

# Fase 2: Validar dados após load
python scripts/python/validate_data.py

# Fase 2: Rollback/Reset do banco
python scripts/python/rollback_db.py

# Fase 3: (Futuro) Rodar testes
pytest tests/

# Fase 4: (Futuro) Explorar análises
jupyter notebook notebooks/exemplo_analises.ipynb
```

---

## 📞 Contato / Dúvidas
Para dúvidas sobre o roadmap, abra uma issue no repositório.
