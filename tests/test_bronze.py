from datetime import UTC, datetime

from alfab.bronze.ingest_batch import (
    bronze_uri,
    export_sql,
    exported_rows,
    external_table_ddl,
    select_sql,
)
from alfab.config import settings

MOD = datetime(2025, 5, 1, tzinfo=UTC)


def test_caminho_unico_por_execucao():
    a = bronze_uri("b", "uf", "20260101T000000Z-aaaaaa", "2026-01-01")
    b = bronze_uri("b", "uf", "20260101T060000Z-bbbbbb", "2026-01-01")
    assert a != b
    assert "/ingestion_date=2026-01-01/run_id=20260101T000000Z-aaaaaa/" in a


def test_export_nunca_sobrescreve_e_usa_parquet_zstd():
    sql = export_sql(settings().entities["uf"], "gs://b/x/*.parquet", MOD)
    assert "overwrite = false" in sql
    assert "format = 'PARQUET'" in sql and "compression = 'ZSTD'" in sql
    assert "WRITE_TRUNCATE" not in sql and "CREATE OR REPLACE" not in sql


def test_select_com_colunas_explicitas_e_metadados():
    sql = select_sql(settings().entities["alunos"], MOD)
    assert "SELECT *" not in sql
    assert "`peso_aluno`" in sql and "`proficiencia`" in sql
    assert "_ingested_at" in sql and "_source_last_modified" in sql


def test_external_table_hive_particionada():
    ddl = external_table_ddl("p.bronze.uf", "gs://b/bronze/uf")
    assert "CREATE EXTERNAL TABLE IF NOT EXISTS" in ddl
    assert "WITH PARTITION COLUMNS (ingestion_date DATE, run_id STRING)" in ddl
    assert "hive_partition_uri_prefix = 'gs://b/bronze/uf'" in ddl


def test_linhas_exportadas_lidas_das_estatisticas_do_job():
    class Job:
        _properties = {"statistics": {"query": {"exportDataStatistics": {"rowCount": "42"}}}}

    class SemStats:
        _properties = {}

    assert exported_rows(Job()) == 42
    assert exported_rows(SemStats()) is None
