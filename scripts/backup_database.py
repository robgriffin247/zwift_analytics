import duckdb
import os
import argparse
from datetime import datetime

prod_db = "md:zwift_analytics_prod"
test_db = "md:zwift_analytics_test"
dev_db = "data/zwift_analytics_dev.duckdb"

DB_MAP = {
    "prod": prod_db,
    "test": test_db,
    "dev": dev_db,
}

def backup_db(source_db: str, backup_dir: str = "data") -> str:
    os.makedirs(backup_dir, exist_ok=True)

    db_name = os.path.basename(source_db.removeprefix("md:").removesuffix(".duckdb"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{db_name}_{timestamp}.duckdb")

    con = duckdb.connect(source_db)
    con.execute(f"ATTACH '{backup_path}' AS backup")
    con.execute(f"COPY FROM DATABASE {db_name} TO backup")
    con.close()

    print(f"✓ Backed up '{source_db}' → '{backup_path}'")
    return backup_path

def main():
    parser = argparse.ArgumentParser(description="Backup a DuckDB/MotherDuck database locally.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--prod", action="store_true", help="Backup production database")
    group.add_argument("-t", "--test", action="store_true", help="Backup test database")
    group.add_argument("-d", "--dev",  action="store_true", help="Backup dev database")

    args = parser.parse_args()

    if args.prod:
        backup_db(DB_MAP["prod"])
    elif args.test:
        backup_db(DB_MAP["test"])
    elif args.dev:
        backup_db(DB_MAP["dev"])


if __name__ == "__main__":
    main()