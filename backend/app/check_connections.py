"""Connectivity checks only: never sends email or prints credentials."""

import smtplib
import ssl

from .config import settings


def main():
    from .mongo import client, database

    try:
        client().admin.command("ping")
        db = database()
        print("Atlas authenticated; database reachable.")
        print("Existing user_details records:", db[settings().user_collection].count_documents({}))
    except Exception as exc:
        print("Atlas connection failed:", type(exc).__name__)
    try:
        with smtplib.SMTP(settings().email_host, settings().email_port, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings().email_user, settings().email_password)
        print("SMTP authentication passed. No email sent.")
    except Exception as exc:
        print("SMTP authentication failed:", type(exc).__name__)


if __name__ == "__main__":
    main()
