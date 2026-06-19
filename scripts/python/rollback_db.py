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

LOG_FILE = LOG_DIR / f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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

def listar_tabelas_por_schema(cursor, schema):
    """Lista todas as tabelas em um schema"""
    try:
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            ORDER BY table_name DESC
        """, (schema,))
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.warning(f"Não foi possível listar tabelas do schema {schema}: {e}")
        return []

def resetar_tabela(cursor, tabela):
    """Reseta uma tabela (deleta dados, resetando sequence)"""
    try:
        cursor.execute(f"TRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE")
        logger.info(f"✓ Tabela {tabela} resetada com sucesso")
        return True
    except psycopg2.errors.UndefinedTable:
        logger.warning(f"⚠ Tabela {tabela} não existe")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao resetar tabela {tabela}: {e}")
        return False

def deletar_dados_tabela(cursor, tabela):
    """Delete dados de uma tabela (sem resetar sequence)"""
    try:
        cursor.execute(f"DELETE FROM {tabela}")
        linhas_deletadas = cursor.rowcount
        logger.info(f"✓ {linhas_deletadas} linhas deletadas de {tabela}")
        return True
    except psycopg2.errors.UndefinedTable:
        logger.warning(f"⚠ Tabela {tabela} não existe")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao deletar dados de {tabela}: {e}")
        return False

def rollback_completo(cursor):
    """Faz rollback completo do ETL - deleta dados em ordem de dependência"""
    logger.info("\n=== Iniciando Rollback Completo ===\n")
    
    # Ordem de deleção (inversa das dependências)
    tabelas_para_deletar = [
        "analytics.fato_saude_municipio",
        "analytics.dim_saude",
        "analytics.dim_municipio",
        "staging.saude_municipios_staging",
        "raw.saude_municipios",
    ]
    
    sucesso = True
    for tabela in tabelas_para_deletar:
        # Tentar resetar com TRUNCATE (mais rápido)
        if not resetar_tabela(cursor, tabela):
            # Se falhar, tentar delete simples
            deletar_dados_tabela(cursor, tabela)
            if not sucesso:
                sucesso = False
    
    logger.info("\n✓ Rollback completo concluído")
    return sucesso

def rollback_parcial_raw(cursor):
    """Rollback apenas da tabela raw (útil para recarregar dados)"""
    logger.info("\n=== Rollback Parcial (Raw) ===\n")
    
    try:
        # Deletar dados das tabelas dependentes primeiro
        tabelas = [
            "analytics.fato_saude_municipio",
            "analytics.dim_saude",
            "analytics.dim_municipio",
            "staging.saude_municipios_staging",
            "raw.saude_municipios",
        ]
        
        for tabela in tabelas:
            resetar_tabela(cursor, tabela)
        
        logger.info("✓ Rollback parcial concluído - pronto para recarregar dados")
        return True
    except Exception as e:
        logger.error(f"✗ Erro no rollback parcial: {e}")
        return False

def listar_status_dados(cursor):
    """Lista o status de dados em cada tabela"""
    logger.info("\n=== Status de Dados ===\n")
    
    tabelas = [
        "raw.saude_municipios",
        "staging.saude_municipios_staging",
        "analytics.dim_municipio",
        "analytics.dim_saude",
        "analytics.fato_saude_municipio",
    ]
    
    for tabela in tabelas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            logger.info(f"  {tabela}: {count} registros")
        except psycopg2.errors.UndefinedTable:
            logger.info(f"  {tabela}: [Não existe]")
        except Exception as e:
            logger.warning(f"  {tabela}: [Erro ao contar - {e}]")

def obter_tamanho_banco(cursor):
    """Obtém informações de tamanho do banco"""
    logger.info("\n=== Tamanho do Banco de Dados ===\n")
    
    try:
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                ROUND(pg_total_relation_size(schemaname||'.'||tablename)/1024/1024, 2) as size_mb
            FROM pg_tables
            WHERE schemaname IN ('raw', 'staging', 'analytics')
            ORDER BY size_mb DESC
        """)
        
        resultados = cursor.fetchall()
        if resultados:
            total_mb = sum(row[2] for row in resultados)
            for schema, tabela, size_mb in resultados:
                logger.info(f"  {schema}.{tabela}: {size_mb} MB")
            logger.info(f"\n  Total: {total_mb} MB")
        else:
            logger.info("  Nenhuma tabela encontrada")
    except Exception as e:
        logger.debug(f"Informações de tamanho não disponíveis: {e}")

def main():
    """Função principal"""
    logger.info("Ferramenta de Rollback/Reset do Banco de Dados ETL")
    logger.info("=" * 50)
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        # Menu de opções
        print("\nOpções:")
        print("1 - Listar status de dados")
        print("2 - Listar tamanho do banco")
        print("3 - Rollback da tabela raw (recarregar dados)")
        print("4 - Rollback completo (deletar tudo)")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == '1':
            listar_status_dados(cursor)
        elif opcao == '2':
            obter_tamanho_banco(cursor)
        elif opcao == '3':
            confirmacao = input("\n⚠️  Deseja fazer rollback da tabela raw? (s/n): ").strip().lower()
            if confirmacao == 's':
                rollback_parcial_raw(cursor)
                conexao.commit()
            else:
                logger.info("Operação cancelada")
        elif opcao == '4':
            confirmacao = input("\n⚠️⚠️  ATENÇÃO! Deseja deletar TODOS os dados? (s/n): ").strip().lower()
            if confirmacao == 's':
                confirmacao2 = input("Tem certeza? Digite 'sim' para confirmar: ").strip().lower()
                if confirmacao2 == 'sim':
                    rollback_completo(cursor)
                    conexao.commit()
                else:
                    logger.info("Operação cancelada")
            else:
                logger.info("Operação cancelada")
        else:
            logger.warning("Opção inválida")
        
        logger.info("\n✓ Operação concluída!")
        cursor.close()
        conexao.close()
        
    except KeyboardInterrupt:
        logger.info("\nOperação cancelada pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"✗ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
