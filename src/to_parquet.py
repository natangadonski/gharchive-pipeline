#Converte um arquivo horário do GH Archive (JSON.gz) para Parquet.
import sys
from pathlib import Path
import duckdb

COLUMNS = {
    "id": "VARCHAR",
    "type": "VARCHAR",
    "actor": "STRUCT(id BIGINT, login VARCHAR)",
    "repo": "STRUCT(id BIGINT, name VARCHAR)",
    "payload": "JSON",
    "public": "BOOLEAN",
    "created_at": "TIMESTAMP",
    "org": "STRUCT(id BIGINT, login VARCHAR)",
}

def _source(raw_path: Path) -> str:
    return (
        f"read_json('{raw_path}', format='newline_delimited', "
        f"columns={COLUMNS})"
    )

def convert(raw_path: Path, out_path: Path) -> int:
    #Converte um arquivo e devolve o número de linhas gravadas
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source = _source(raw_path)

    duckdb.sql(f"""
        COPY (
            SELECT
                CAST(id AS BIGINT) AS id,
                type,
                actor.id AS actor_id,
                actor.login AS actor_login,
                repo.id AS repo_id,
                repo.name AS repo_name,
                org.id AS org_id,
                org.login AS org_login,
                public,
                created_at,
                payload
            FROM {source}
        ) TO '{out_path}' (FORMAT parquet, COMPRESSION zstd)

    """)

    rows_in = duckdb.sql(f"SELECT count(*) FROM {source}").fetchone()[0]
    rows_out = duckdb.sql(f"SELECT count(*) FROM read_parquet('{out_path}')").fetchone()[0]
    if rows_in != rows_out:
        raise ValueError(f"Contagem diferente: {rows_in} entrada, {rows_out} saída")
    return rows_out

if __name__ == "__main__":
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    print(f"{convert(raw, out)} linhas gravadas em {out}") 