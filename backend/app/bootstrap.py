"""Initialize the selected database, then add original content idempotently."""

from .config import settings
from .seed import seed


def main():
    if settings().database_url.startswith("mongodb"):
        from .mongo import ensure_indexes

        ensure_indexes()
    else:
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config("alembic.ini"), "head")
    seed()


if __name__ == "__main__":
    main()
