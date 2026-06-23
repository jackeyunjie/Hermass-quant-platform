"""DuckDB connection helper.

Provides a single connection entry point that disables extension autoloading
and autoinstallation. DuckDB's default autoload behaviour can trigger network
requests (e.g. for the parquet extension) which stall in offline or
proxy-restricted environments; the bundled parquet extension works without it.
"""

from __future__ import annotations

import duckdb


def connect_duckdb(database: str, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection with extension autoload disabled."""
    con = duckdb.connect(database, read_only=read_only)
    con.execute("SET autoinstall_known_extensions=false")
    con.execute("SET autoload_known_extensions=false")
    return con
