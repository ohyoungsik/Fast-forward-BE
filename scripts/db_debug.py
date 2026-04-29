from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal


def main() -> None:
    print("ENV:", settings.ENV)
    print("DB_URL:", settings.DB_URL)

    db = SessionLocal()
    try:
        print("current_schema:", db.execute(text("select current_schema()")).scalar())
        print("search_path:", db.execute(text("show search_path")).scalar())

        tables = db.execute(
            text(
                """
                select table_schema, table_name
                from information_schema.tables
                where table_type = 'BASE TABLE'
                  and table_catalog = current_database()
                order by table_schema, table_name
                limit 80
                """
            )
        ).fetchall()
        print("tables(limit=80):", tables)

        candidates = ["log", "logs", "public.log", "public.logs"]
        for t in candidates:
            try:
                cnt = db.execute(text(f"select count(*) from {t}")).scalar()
                print(f"count({t}) =", cnt)
            except Exception as e:
                print(f"count({t}) ERROR:", repr(e))
    finally:
        db.close()


if __name__ == "__main__":
    main()

