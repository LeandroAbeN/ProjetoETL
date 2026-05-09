#!/usr/bin/env python3

import psycopg2
import csv
import os
from datetime import datetime

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'etl_portfolio'),
    'user': os.getenv('DB_USER', 'etl_user'),
    'password': os.getenv('DB_PASSWORD', 'etl_password123')
}

CSV_FILE = './data/raw/saude_municipios.csv'

def conectar_banco():
    """Connectionect ao PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"Conexão estabelecida com {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar: {e}")
        exit(1)

def carregar_csv_para_raw(conn):
    """Carrega CSV para a tabela raw"""
    try:
        cur = conn.cursor()
        
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            dados = list(reader)
        
        colunas = list(dados[0].keys())
        
        insert_sql = f"""
            INSERT INTO raw.saude_municipios 
            ({', '.join(colunas)}) 
            VALUES ({', '.join(['%s'] * len(colunas))})
        """
        
        for linha in dados:
            valores = [linha[col] for col in colunas]
            cur.execute(insert_sql, valores)
        
        conn.commit()
        print(f"{len(dados)} registros carregados")
        return len(dados)
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao carregar dados: {e}")
        exit(1)
    finally:
        cur.close()

def executar_transformacoes(conn):
    """Executa scripts SQL"""
    scripts = [
        './scripts/sql/03_staging_transformations.sql',
        './scripts/sql/04_dm_transformations.sql',
        './scripts/sql/05_analytics_views.sql'
    ]
    
    cur = conn.cursor()
    
    for script in scripts:
        try:
            with open(script, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            cur.execute(sql)
            conn.commit()
            print(f"{os.path.basename(script)}")
            
        except Exception as e:
            conn.rollback()
            print(f"Erro: {e}")
            exit(1)
    
    cur.close()

def gerar_relatorio(conn):
    """Gera relatório"""
    cur = conn.cursor()
    
    print("\nResumo da execução:")
    
    for schema, tabela in [('raw', 'saude_municipios'), 
                           ('staging', 'saude_municipios'), 
                           ('dm', 'saude_municipios')]:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{tabela}")
        count = cur.fetchone()[0]
        print(f"{schema}: {count} registros")
    
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.views 
        WHERE table_schema = 'dm'
    """)
    views_count = cur.fetchone()[0]
    print(f"Views criadas: {views_count}")
    
    cur.close()

def main():
    """Executa o pipeline ETL"""
    conn = conectar_banco()
    
    print("Iniciando ETL...")
    carregar_csv_para_raw(conn)
    executar_transformacoes(conn)
    gerar_relatorio(conn)
    
    conn.close()
    print("Concluído!")

if __name__ == '__main__':
    main()

