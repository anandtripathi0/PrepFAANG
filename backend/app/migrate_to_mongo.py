"""Non-destructive import of the existing local development database into Atlas."""

from pathlib import Path

from pymongo import UpdateOne
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from . import models  # noqa: F401
from .db import Base
from .mongo import collection_name, database, ensure_indexes


def main():
    source = Path(__file__).resolve().parents[1] / "prepforge.db"
    if not source.exists():
        raise SystemExit("No legacy SQLite database found. Run the seed command instead.")
    ensure_indexes()
    with Session(create_engine("sqlite:///" + source.as_posix())) as sql:
        for mapper in sorted(Base.registry.mappers, key=lambda m: m.local_table.name):
            model = mapper.class_
            primary = list(mapper.local_table.primary_key.columns)[0].name
            rows = sql.scalars(select(model)).all()
            requests = []
            for row in rows:
                values = {c.name: getattr(row, c.name) for c in mapper.local_table.columns}
                requests.append(UpdateOne({"_id": values[primary]}, {"$setOnInsert": values}, upsert=True))
            if requests:
                result = database()[collection_name(model)].bulk_write(requests, ordered=True)
                print(
                    collection_name(model), "inserted:", result.upserted_count, "already present:", result.matched_count
                )
    print("Migration complete. Existing Atlas records and the local database were preserved.")


if __name__ == "__main__":
    main()
