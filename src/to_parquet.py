"""Convert an hourly GH Archive file (JSON.gz) to Parquet.

Usage:
    python3 src/to_parquet.py <raw_file.json.gz> <output.parquet>
"""
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
    """Build the DuckDB read_json expression for a raw GH Archive file.

    Args:
        raw_path: Path to the hourly .json.gz file.

    Returns:
        A SQL fragment meant to be used right after FROM.
    """
    return (
        f"read_json('{raw_path}', format='newline_delimited', "
        f"columns={COLUMNS})"
    )

def convert(raw_path: Path, out_path: Path) -> int:
    """Convert one raw file to Parquet and validate the row count.

    Reads the file using an explicit schema, flattens actor, repo and org
    into columns, keeps the payload as JSON text and writes a
    zstd-compressed Parquet file.

    Args:
        raw_path: Path to the hourly .json.gz file.
        out_path: Path where the Parquet file will be written.

    Returns:
        The number of rows written.

    Raises:
        ValueError: If the output row count differs from the input.
    """
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
        raise ValueError(f"Row count mismatch: {rows_in} in, {rows_out} out")
    return rows_out

if __name__ == "__main__":
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    print(f"{convert(raw, out)} rows written to {out}") 