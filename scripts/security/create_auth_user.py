from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from api.security import create_or_update_user, get_auth_dsn  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update auth user in PostgreSQL")
    parser.add_argument("--username", required=True, help="Auth username")
    parser.add_argument(
        "--role",
        default="viewer",
        choices=["viewer", "operator", "admin"],
        help="Role for the user",
    )
    parser.add_argument(
        "--password",
        default="",
        help="Password (optional). If omitted, secure prompt will be used.",
    )
    parser.add_argument(
        "--dsn",
        default="",
        help="Optional DSN override. Defaults to ORACLE_AUTH_POSTGRES_DSN/ORACLE_POSTGRES_DSN.",
    )
    return parser.parse_args()


def get_password_from_prompt() -> str:
    first = getpass.getpass("Password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        raise ValueError("Password confirmation does not match")
    if not first:
        raise ValueError("Password must not be empty")
    return first


def main() -> int:
    args = parse_args()

    dsn = args.dsn.strip() or get_auth_dsn()
    if not dsn:
        print("ERROR: Missing auth DSN. Set ORACLE_AUTH_POSTGRES_DSN or ORACLE_POSTGRES_DSN.")
        return 1

    password = args.password
    if not password:
        try:
            password = get_password_from_prompt()
        except ValueError as exc:
            print(f"ERROR: {str(exc)}")
            return 1

    try:
        create_or_update_user(
            username=args.username,
            password=password,
            role=args.role,
            dsn=dsn,
        )
    except Exception as exc:
        print(f"ERROR: Failed to create user: {str(exc)}")
        return 1

    print(f"OK: user '{args.username}' saved with role '{args.role}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
