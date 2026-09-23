import argparse

from sqlalchemy import select

from .db import SessionLocal
from .models import User


def main():
    parser = argparse.ArgumentParser(description="PrepFaang account administration")
    parser.add_argument("command", choices=["make-admin"])
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if not user:
            raise SystemExit("Register this account in the app first.")
        user.role = "admin"
        db.commit()
        print("Administrator role granted.")


if __name__ == "__main__":
    main()
