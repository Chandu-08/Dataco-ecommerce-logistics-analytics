"""Upload original DataCo order or clickstream CSV to SQL Server staging.

Prerequisites: pip install pyodbc; install Microsoft ODBC Driver 18; run
sql/01_database_setup.sql; set DATACO_ODBC_CONNECTION to a connection string.
Examples:
  python python/import_raw_sql_server.py --dataset orders --csv data/raw/DataCoSupplyChainDataset.csv
  python python/import_raw_sql_server.py --dataset logs --csv data/raw/tokenized_access_logs.csv
Use --replace only when intentionally re-importing the same source.
"""
import argparse
import csv
import os
from pathlib import Path

try:
    import pyodbc
except ImportError as exc:
    raise SystemExit("Install pyodbc and the Microsoft SQL Server ODBC driver") from exc


def ident(name):
    if len(name) > 128:
        raise ValueError(f"SQL Server column name is too long: {name!r}")
    return '[' + name.replace(']', ']]') + ']'


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--dataset', choices=('orders','logs'), default='orders')
    cli.add_argument('--csv', type=Path)
    cli.add_argument('--replace', action='store_true', help='Delete existing staging rows and re-import')
    args = cli.parse_args()
    connection = os.getenv('DATACO_ODBC_CONNECTION')
    if not connection:
        raise SystemExit('Set DATACO_ODBC_CONNECTION; do not put credentials in the project')
    source = args.csv or Path(__file__).resolve().parents[1] / 'data/raw' / ('DataCoSupplyChainDataset.csv' if args.dataset == 'orders' else 'tokenized_access_logs.csv')
    target = 'DataCoRaw' if args.dataset == 'orders' else 'DataCoAccessLogs'
    expected = 53 if args.dataset == 'orders' else 8
    encoding = 'latin1' if args.dataset == 'orders' else 'utf-8-sig'
    with source.open(newline='', encoding=encoding) as f:
        reader = csv.reader(f)
        columns = next(reader)
        if len(columns) != expected or len(set(columns)) != len(columns):
            raise ValueError(f'Expected {expected} unique source column names')
        if args.dataset == 'logs' and set(columns) != {'Product','Category','Date','Month','Hour','Department','ip','url'}:
            raise ValueError('Unexpected clickstream column names')
        # Verified Kaggle copy has maximum cell width 94 chars; reserve room
        # for a different source revision while keeping ODBC batches bounded.
        ddl = ',\n'.join(ident(c) + ' nvarchar(512) NULL' for c in columns)
        insert = (f'INSERT INTO staging.{target} (' + ','.join(map(ident, columns)) + ') VALUES ('
                  + ','.join('?' for _ in columns) + ')')
        with pyodbc.connect(connection, autocommit=False) as db:
            cur = db.cursor()
            exists = cur.execute(f"SELECT OBJECT_ID('staging.{target}','U')").fetchval()
            if exists:
                if not args.replace:
                    raise SystemExit(f'staging.{target} already exists. Use --replace to re-import deliberately.')
                cur.execute(f'DROP TABLE staging.{target}')
            cur.execute(f'CREATE TABLE staging.{target} (source_row_id bigint IDENTITY(1,1) NOT NULL PRIMARY KEY, ' + ddl + ')')
            db.commit()
            cur.fast_executemany = True
            count, batch = 0, []
            for row in reader:
                if len(row) != len(columns):
                    raise ValueError(f'CSV record {count+2} has {len(row)} fields; expected {len(columns)}')
                if any(len(cell) > 512 for cell in row):
                    raise ValueError(f'CSV record {count+2} exceeds 512 chars in a staged field')
                batch.append(tuple(None if cell == '' else cell for cell in row))
                if len(batch) == 200:
                    cur.executemany(insert, batch)
                    db.commit()
                    count += len(batch)
                    batch.clear()
            if batch:
                cur.executemany(insert, batch)
                db.commit()
                count += len(batch)
            actual = cur.execute(f'SELECT COUNT_BIG(*) FROM staging.{target}').fetchval()
            if actual != count:
                raise AssertionError(f'Import row count differs: CSV={count}, SQL={actual}')
            print(f'Imported {actual:,} source rows, {len(columns)} original fields into staging.{target}')
            print('Raw staging includes personal or IP-like fields. Restrict staging access and run SQL cleaning next.')


if __name__ == '__main__':
    main()
