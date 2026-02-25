import duckdb
import os

prod_db = "md:zwift_analytics_prod"
dev_db = "data/zwift_analytics_dev.duckdb"

def clone_prod_to_dev():
    motherduck_token = os.getenv("MOTHERDUCK_TOKEN")

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
