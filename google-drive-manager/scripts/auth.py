#!/usr/bin/env python3
"""
Google Drive Service Account authentication.
Designed for AI Agent automation - no browser interaction required.

Usage:
    python scripts/auth.py status              # Check credentials
    python scripts/auth.py validate            # Validate and test API access
"""

import json
import os
import sys
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]
DEFAULT_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")


def load_credentials(credentials_path: str = DEFAULT_CREDENTIALS_PATH):
    """Load Service Account credentials from JSON file."""
    if not os.path.exists(credentials_path):
        print(f"Error: credentials file not found: {credentials_path}", file=sys.stderr)
        print("Set GOOGLE_CREDENTIALS_PATH env var or place credentials.json in current directory.", file=sys.stderr)
        sys.exit(1)

    try:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )
        return creds
    except (ValueError, KeyError) as e:
        print(f"Error: invalid credentials file: {e}", file=sys.stderr)
        sys.exit(1)


def build_service(credentials_path: str = DEFAULT_CREDENTIALS_PATH):
    """Build and return an authenticated Google Drive API service."""
    creds = load_credentials(credentials_path)
    return build("drive", "v3", credentials=creds)


def get_service_account_email(credentials_path: str = DEFAULT_CREDENTIALS_PATH) -> Optional[str]:
    """Extract service account email from credentials file."""
    try:
        with open(credentials_path) as f:
            data = json.load(f)
        return data.get("client_email")
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Google Drive Service Account auth management")
    subparsers = parser.add_subparsers(dest="command")

    status_parser = subparsers.add_parser("status", help="Show credentials status")
    status_parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH)

    validate_parser = subparsers.add_parser("validate", help="Validate credentials by calling API")
    validate_parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH)

    args = parser.parse_args()

    if args.command == "status":
        path = args.credentials
        if os.path.exists(path):
            email = get_service_account_email(path)
            print(f"Status: credentials found at '{path}'")
            if email:
                print(f"Service Account: {email}")
        else:
            print(f"Status: credentials NOT found at '{path}'")
            print("Set GOOGLE_CREDENTIALS_PATH or place credentials.json in current directory.")
            sys.exit(1)

    elif args.command == "validate":
        print("Validating credentials...", file=sys.stderr)
        try:
            service = build_service(args.credentials)
            service.files().list(pageSize=1, fields="files(id)").execute()
            email = get_service_account_email(args.credentials)
            print(f"Validation successful!")
            if email:
                print(f"Service Account: {email}")
        except HttpError as e:
            print(f"Validation failed: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
