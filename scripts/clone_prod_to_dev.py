import duckdb
import os

prod_db = "md:zwift_analytics_prod"
dev_db = "data/zwift_analytics_dev.duckdb"

def clone_prod_to_dev():
    motherduck_token = os.getenv("MOTHERDUCK_TOKEN")

    # Ensure we start from a clean local database file before cloning.
    if os.path.exists(dev_db):
        os.remove(dev_db)
    wal_file = f"{dev_db}.wal"
    if os.path.exists(wal_file):
        os.remove(wal_file)

    with duckdb.connect() as con:
        con.sql("INSTALL motherduck;")
        con.sql("LOAD motherduck;")
        con.sql(f"SET motherduck_token='{motherduck_token}';")
        con.sql(f"""
            ATTACH '{prod_db}' as prod_db;
            ATTACH '{dev_db}' as dev_db;
            COPY FROM DATABASE prod_db TO dev_db;
        """)

    return f"Cloned prod to {dev_db}"


if __name__=="__main__":
    print(clone_prod_to_dev())
