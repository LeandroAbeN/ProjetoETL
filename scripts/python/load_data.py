#!/usr/bin/env python3

import psycopg2
import csv
import os
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
LOG_DIR = Path('./logs')
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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

CSV_FILE = './data/raw/saude_municipios.csv'

def validar_prerequisitos():
    """Valida pré-requisitos antes de iniciar o ETL"""
    logger.info("Validando pré-requisitos...")
    
    # Verificar se o arquivo CSV existe
    if not Path(CSV_FILE).exists():
        logger.error(f"Arquivo CSV não encontrado: {CSV_FILE}")
        raise FileNotFoundError(f"Arquivo não encontrado: {CSV_FILE}")
    
    logger.info(f"✓ Arquivo CSV encontrado: {CSV_FILE}")
    return True

def conectar_banco():
    """Conectar ao PostgreSQL"""
    try:
        logger.info(f"Conectando ao banco de dados em {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✓ Conexão estabelecida com sucesso")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        raise

def validar_banco(conn):
    """Valida se os schemas e tabelas existem"""
    logger.info("Validando schemas e tabelas...")
    cur = conn.cursor()
    
    try:
        # Verificar schemas
        schemas_esperados = ['raw', 'staging', 'dm', 'analytics']
        for schema in schemas_esperados:
            cur.execute("""
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = %s
            """, (schema,))
            
            if not cur.fetchone():
                logger.warning(f"Schema '{schema}' não encontrado. Execute 01_create_schemas.sql primeiro.")
                return False
            logger.info(f"✓ Schema '{schema}' encontrado")
        
        # Verificar tabela RAW
        cur.execute("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'raw' AND table_name = 'saude_municipios'
        """)
        
        if not cur.fetchone():
            logger.warning("Tabela 'raw.saude_municipios' não encontrada. Execute 02_create_raw_tables.sql primeiro.")
            return False
        
        logger.info("✓ Tabela 'raw.saude_municipios' encontrada")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Erro ao validar banco: {e}")
        return False
    finally:
        cur.close()


def carregar_csv_para_raw(conn):
    """Carrega CSV para a tabela raw.saude_municipios"""
    logger.info("Carregando CSV para camada RAW...")
    try:
        cur = conn.cursor()
        
        # Ler CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            dados = list(reader)
        
        if not dados:
            logger.error("Arquivo CSV vazio")
            return 0
        
        logger.info(f"Lendo {len(dados)} registros do CSV...")
        
        colunas = list(dados[0].keys())
        
        insert_sql = f"""
            INSERT INTO raw.saude_municipios 
            ({', '.join(colunas)}) 
            VALUES ({', '.join(['%s'] * len(colunas))})
        """
        
        # Inserir registros
        for idx, linha in enumerate(dados):
            valores = [linha[col] for col in colunas]
            try:
                cur.execute(insert_sql, valores)
            except Exception as e:
                logger.warning(f"Erro na linha {idx + 1}: {e}")
                conn.rollback()
                raise
        
        conn.commit()
        logger.info(f"✓ {len(dados)} registros carregados com sucesso")
        return len(dados)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao carregar dados: {e}")
        raise
    finally:
        cur.close()


def executar_transformacoes(conn):
    """Executa scripts SQL das transformações"""
    logger.info("Executando transformações...")
    
    # Nota: Os scripts 01 e 02 já devem ter sido executados manualmente
    scripts = [
        './scripts/sql/03_staging_transformations.sql',
        './scripts/sql/04_dm_transformations.sql',
        './scripts/sql/05_dm_optimization.sql',
        './scripts/sql/06_analytics_views.sql'  # ← Corrigido de 05_analytics_views.sql
    ]
    
    cur = conn.cursor()
    
    for script_path in scripts:
        try:
            # Verificar se arquivo existe
            if not Path(script_path).exists():
                logger.warning(f"Script não encontrado: {script_path}")
                continue
            
            logger.info(f"Executando: {os.path.basename(script_path)}...")
            
            with open(script_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            cur.execute(sql)
            conn.commit()
            logger.info(f"✓ {os.path.basename(script_path)} executado com sucesso")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao executar {os.path.basename(script_path)}: {e}")
            raise
    
    cur.close()


def gerar_relatorio(conn):
    """Gera relatório resumido do ETL"""
    logger.info("Gerando relatório...")
    cur = conn.cursor()
    
    try:
        print("\n" + "="*60)
        print("RELATÓRIO DE EXECUÇÃO DO ETL")
        print("="*60)
        
        # Contar registros em cada camada
        for schema, tabela in [('raw', 'saude_municipios'), 
                               ('staging', 'saude_municipios'), 
                               ('dm', 'saude_municipios')]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{tabela}")
                count = cur.fetchone()[0]
                logger.info(f"{schema.upper()}: {count} registros")
                print(f"{schema.upper():12} │ {count:6} registros")
            except Exception as e:
                logger.warning(f"Não foi possível contar registros em {schema}.{tabela}: {e}")
                print(f"{schema.upper():12} │ [erro ao contar]")
        
        # Contar views na camada ANALYTICS (corrigido de 'dm')
        try:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.views 
                WHERE table_schema = 'analytics'
            """)
            views_count = cur.fetchone()[0]
            logger.info(f"Views criadas na camada ANALYTICS: {views_count}")
            print(f"{'ANALYTICS':12} │ {views_count:6} views")
        except Exception as e:
            logger.warning(f"Não foi possível contar views: {e}")
            print(f"{'ANALYTICS':12} │ [erro ao contar]")
        
        print("="*60)
        print(f"Logs salvos em: {LOG_FILE}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
    finally:
        cur.close()


def main():
    """Executa o pipeline ETL completo"""
    try:
        logger.info("="*60)
        logger.info("INICIANDO PIPELINE ETL")
        logger.info("="*60)
        
        # 1. Validar pré-requisitos
        validar_prerequisitos()
        
        # 2. Conectar ao banco
        conn = conectar_banco()
        
        # 3. Validar banco de dados
        if not validar_banco(conn):
            logger.error("Banco de dados não está configurado corretamente.")
            logger.error("Execute os scripts SQL na seguinte ordem:")
            logger.error("  1. scripts/sql/01_create_schemas.sql")
            logger.error("  2. scripts/sql/02_create_raw_tables.sql")
            raise RuntimeError("Banco não configurado")
        
        # 4. Carregar dados
        registros_carregados = carregar_csv_para_raw(conn)
        
        # 5. Executar transformações
        executar_transformacoes(conn)
        
        # 6. Gerar relatório
        gerar_relatorio(conn)
        
        logger.info("="*60)
        logger.info("✓ PIPELINE ETL CONCLUÍDO COM SUCESSO")
        logger.info("="*60)
        
        conn.close()
        
    except Exception as e:
        logger.error(f"✗ ERRO NO PIPELINE ETL: {e}")
        logger.error("Verifique o arquivo de log para mais detalhes")
        sys.exit(1)

if __name__ == '__main__':
    main()

