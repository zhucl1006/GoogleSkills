#!/usr/bin/env python3
"""
Google Drive file operations for AI Agents.
All operations return structured JSON for easy parsing.

Usage:
    python scripts/drive.py upload <local_path> [--name NAME] [--folder FOLDER_ID]
    python scripts/drive.py search <query>
    python scripts/drive.py download <file_id> <local_path>
    python scripts/drive.py update <file_id> <local_path>
    python scripts/drive.py delete <file_id> [--permanent]
    python scripts/drive.py list [FOLDER_ID]
"""

import argparse
import json
import os
import sys

from auth import build_service, DEFAULT_CREDENTIALS_PATH
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io


def _print(data: dict):
    """Print result as formatted JSON."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def upload(local_path: str, name: str = None, folder_id: str = None,
           credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """Upload a local file to Google Drive."""
    if not os.path.exists(local_path):
        return {"status": "error", "message": f"Local file not found: {local_path}"}

    service = build_service(credentials)
    file_name = name or os.path.basename(local_path)
    metadata = {"name": file_name}
    if folder_id:
        metadata["parents"] = [folder_id]

    try:
        media = MediaFileUpload(local_path, resumable=True)
        file = service.files().create(
            body=metadata, media_body=media, fields="id, name, webViewLink"
        ).execute()
        return {
            "status": "success",
            "message": f"Uploaded '{file_name}'",
            "data": {"file_id": file["id"], "name": file["name"], "web_view_link": file.get("webViewLink")}
        }
    except HttpError as e:
        return {"status": "error", "message": f"Upload failed: {e}"}


def search(query: str, limit: int = 10,
           credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """Search files by keyword (excludes trashed files)."""
    service = build_service(credentials)
    drive_query = f"name contains '{query}' and trashed = false"

    try:
        results = service.files().list(
            q=drive_query,
            pageSize=limit,
            fields="files(id, name, mimeType, webViewLink, modifiedTime)"
        ).execute()
        files = results.get("files", [])
        return {
            "status": "success",
            "message": f"Found {len(files)} file(s)",
            "data": files
        }
    except HttpError as e:
        return {"status": "error", "message": f"Search failed: {e}"}


def download(file_id: str, local_path: str,
             credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """Download a file from Google Drive. Does not support native Google Docs/Sheets."""
    service = build_service(credentials)

    try:
        # Check mime type first
        meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        if meta.get("mimeType", "").startswith("application/vnd.google-apps."):
            return {
                "status": "error",
                "message": f"Cannot download Google Workspace file ({meta['mimeType']}). Export it first.",
                "file_name": meta.get("name")
            }

        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(os.path.abspath(local_path)) or ".", exist_ok=True)
        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        return {
            "status": "success",
            "message": f"Downloaded to {local_path}",
            "data": {"local_path": os.path.abspath(local_path), "file_name": meta.get("name")}
        }
    except HttpError as e:
        return {"status": "error", "message": f"Download failed: {e}"}


def update(file_id: str, local_path: str,
           credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """Overwrite an existing Drive file with local file content."""
    if not os.path.exists(local_path):
        return {"status": "error", "message": f"Local file not found: {local_path}"}

    service = build_service(credentials)
    try:
        media = MediaFileUpload(local_path, resumable=True)
        file = service.files().update(
            fileId=file_id, media_body=media, fields="id, name, webViewLink"
        ).execute()
        return {
            "status": "success",
            "message": f"Updated '{file['name']}'",
            "data": {"file_id": file["id"], "name": file["name"], "web_view_link": file.get("webViewLink")}
        }
    except HttpError as e:
        return {"status": "error", "message": f"Update failed: {e}"}


def delete(file_id: str, permanent: bool = False,
           credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """Move file to trash (default) or permanently delete."""
    service = build_service(credentials)
    try:
        if permanent:
            service.files().delete(fileId=file_id).execute()
            action = "permanently deleted"
        else:
            service.files().update(fileId=file_id, body={"trashed": True}).execute()
            action = "moved to trash"
        return {"status": "success", "message": f"File {file_id} {action}"}
    except HttpError as e:
        return {"status": "error", "message": f"Delete failed: {e}"}


def list_files(folder_id: str = None, limit: int = 20,
               credentials: str = DEFAULT_CREDENTIALS_PATH) -> dict:
    """List files in a folder or root directory."""
    service = build_service(credentials)
    params = {
        "pageSize": limit,
        "fields": "files(id, name, mimeType, modifiedTime)"
    }
    if folder_id:
        params["q"] = f"'{folder_id}' in parents and trashed = false"

    try:
        results = service.files().list(**params).execute()
        files = results.get("files", [])
        return {"status": "success", "message": f"Listed {len(files)} file(s)", "data": files}
    except HttpError as e:
        return {"status": "error", "message": f"List failed: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Google Drive operations for AI Agents")
    parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials.json")
    subparsers = parser.add_subparsers(dest="command")

    # upload
    p = subparsers.add_parser("upload", help="Upload a local file")
    p.add_argument("local_path")
    p.add_argument("--name", help="Custom filename on Drive")
    p.add_argument("--folder", dest="folder_id", help="Target folder ID")

    # search
    p = subparsers.add_parser("search", help="Search files by keyword")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)

    # download
    p = subparsers.add_parser("download", help="Download a file")
    p.add_argument("file_id")
    p.add_argument("local_path")

    # update
    p = subparsers.add_parser("update", help="Overwrite a Drive file")
    p.add_argument("file_id")
    p.add_argument("local_path")

    # delete
    p = subparsers.add_parser("delete", help="Delete a file")
    p.add_argument("file_id")
    p.add_argument("--permanent", action="store_true", help="Permanently delete (default: trash)")

    # list
    p = subparsers.add_parser("list", help="List files in a folder")
    p.add_argument("folder_id", nargs="?", default=None)
    p.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    dispatch = {
        "upload":   lambda: upload(args.local_path, args.name, args.folder_id, args.credentials),
        "search":   lambda: search(args.query, args.limit, args.credentials),
        "download": lambda: download(args.file_id, args.local_path, args.credentials),
        "update":   lambda: update(args.file_id, args.local_path, args.credentials),
        "delete":   lambda: delete(args.file_id, args.permanent, args.credentials),
        "list":     lambda: list_files(args.folder_id, args.limit, args.credentials),
    }

    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)

    _print(dispatch[args.command]())


if __name__ == "__main__":
    main()
