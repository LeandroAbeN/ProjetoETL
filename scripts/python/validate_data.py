#!/usr/bin/env python3

import psycopg2
import os
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
LOG_DIR = Path('./logs')
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'etl_portfolio'),
    'user': os.getenv('DB_USER', 'etl_user'),
    'password': os.getenv('DB_PASSWORD', 'etl_password123')
}

def conectar_banco():
    """Conectar ao PostgreSQL"""
    try:
        conexao = psycopg2.connect(**DB_CONFIG)
        logger.info("✓ Conexão com o banco estabelecida")
        return conexao
    except Exception as e:
        logger.error(f"✗ Erro ao conectar no banco: {e}")
        raise

def validar_contagem_registros(cursor):
    """Valida a contagem de registros em cada etapa"""
    logger.info("\n=== Validação de Contagem de Registros ===")
    
    validacoes = [
        ("raw.saude_municipios", "Tabela Raw"),
        ("staging.saude_municipios_staging", "Tabela Staging"),
        ("analytics.dim_municipio", "Dimensão Municipio"),
        ("analytics.dim_saude", "Dimensão Saúde"),
        ("analytics.fato_saude_municipio", "Tabela de Fatos"),
    ]
    
    for tabela, descricao in validacoes:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            logger.info(f"✓ {descricao} ({tabela}): {count} registros")
        except psycopg2.errors.UndefinedTable:
            logger.warning(f"⚠ {descricao} ({tabela}): Tabela não existe ou não foi criada ainda")
        except Exception as e:
            logger.error(f"✗ Erro ao contar registros em {tabela}: {e}")

def validar_nulos(cursor):
    """Verifica colunas críticas com valores nulos"""
    logger.info("\n=== Validação de Valores Nulos ===")
    
    validacoes = [
        ("raw.saude_municipios", ["municipio", "uf", "populacao"]),
        ("staging.saude_municipios_staging", ["municipio", "uf"]),
        ("analytics.dim_municipio", ["cod_municipio"]),
        ("analytics.dim_saude", ["cod_saude"]),
    ]
    
    for tabela, colunas in validacoes:
        try:
            for coluna in colunas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} IS NULL")
                nulos = cursor.fetchone()[0]
                if nulos == 0:
                    logger.info(f"✓ {tabela}.{coluna}: Sem valores nulos")
                else:
                    logger.warning(f"⚠ {tabela}.{coluna}: {nulos} valores nulos encontrados")
        except psycopg2.errors.UndefinedTable:
            logger.warning(f"⚠ Tabela {tabela} não existe ou não foi criada ainda")
        except Exception as e:
            logger.error(f"✗ Erro ao validar nulos em {tabela}: {e}")

def validar_ranges(cursor):
    """Valida ranges de valores numéricos"""
    logger.info("\n=== Validação de Ranges ===")
    
    validacoes = [
        ("raw.saude_municipios", "populacao", 0, None, "População deve ser >= 0"),
        ("raw.saude_municipios", "casos_covid_2023", 0, None, "Casos COVID deve ser >= 0"),
        ("raw.saude_municipios", "obitos_covid_2023", 0, None, "Óbitos COVID deve ser >= 0"),
        ("raw.saude_municipios", "taxa_cobertura_vacina", 0, 100, "Taxa de cobertura deve estar entre 0 e 100"),
        ("raw.saude_municipios", "pessoas_testadas", 0, None, "Pessoas testadas deve ser >= 0"),
    ]
    
    for tabela, coluna, min_val, max_val, descricao in validacoes:
        try:
            if max_val is None:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {tabela} WHERE {coluna} < %s OR {coluna} IS NULL",
                    (min_val,)
                )
                invalidos = cursor.fetchone()[0]
                if invalidos == 0:
                    logger.info(f"✓ {tabela}.{coluna}: {descricao}")
                else:
                    logger.warning(f"⚠ {tabela}.{coluna}: {invalidos} valores fora do range")
            else:
                cursor.execute(
                    f"SELECT COUNT(*) FROM {tabela} WHERE ({coluna} < %s OR {coluna} > %s) AND {coluna} IS NOT NULL",
                    (min_val, max_val)
                )
                invalidos = cursor.fetchone()[0]
                if invalidos == 0:
                    logger.info(f"✓ {tabela}.{coluna}: {descricao}")
                else:
                    logger.warning(f"⚠ {tabela}.{coluna}: {invalidos} valores fora do range [{min_val}, {max_val}]")
        except psycopg2.errors.UndefinedTable:
            logger.warning(f"⚠ Tabela {tabela} não existe ou não foi criada ainda")
        except Exception as e:
            logger.error(f"✗ Erro ao validar range em {tabela}.{coluna}: {e}")

def validar_integridade_referencial(cursor):
    """Valida integridade referencial entre tabelas"""
    logger.info("\n=== Validação de Integridade Referencial ===")
    
    try:
        # Verificar se há registros orfãos na tabela de fatos
        cursor.execute("""
            SELECT COUNT(*) FROM analytics.fato_saude_municipio f
            WHERE NOT EXISTS (SELECT 1 FROM analytics.dim_municipio d WHERE f.cod_municipio = d.cod_municipio)
            AND EXISTS (SELECT 1 FROM analytics.dim_municipio LIMIT 1)
        """)
        orfaos_municipio = cursor.fetchone()[0]
        if orfaos_municipio == 0:
            logger.info("✓ Integridade referencial em dim_municipio: OK")
        else:
            logger.warning(f"⚠ Registros orfãos em dim_municipio: {orfaos_municipio}")
    except Exception as e:
        logger.debug(f"Validação de integridade referencial não aplicável: {e}")

def gerar_relatorio(cursor):
    """Gera um relatório resumido da qualidade dos dados"""
    logger.info("\n=== Relatório Resumido ===")
    
    try:
        cursor.execute("""
            SELECT 
                'raw.saude_municipios' as tabela,
                COUNT(*) as total,
                SUM(CASE WHEN municipio IS NULL THEN 1 ELSE 0 END) as nulos_municipio,
                MIN(populacao) as min_populacao,
                MAX(populacao) as max_populacao
            FROM raw.saude_municipios
        """)
        resultado = cursor.fetchone()
        if resultado:
            logger.info(f"Tabela: {resultado[0]}")
            logger.info(f"  Total de registros: {resultado[1]}")
            logger.info(f"  Valores nulos (municipio): {resultado[2]}")
            logger.info(f"  População (min-max): {resultado[3]}-{resultado[4]}")
    except Exception as e:
        logger.debug(f"Relatório não disponível: {e}")

def main():
    """Função principal"""
    logger.info("Iniciando validação de dados...")
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        # Executar validações
        validar_contagem_registros(cursor)
        validar_nulos(cursor)
        validar_ranges(cursor)
        validar_integridade_referencial(cursor)
        gerar_relatorio(cursor)
        
        logger.info("\n✓ Validação de dados concluída com sucesso!")
        cursor.close()
        conexao.close()
        
    except Exception as e:
        logger.error(f"✗ Erro durante validação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
