#!/usr/bin/env python3
"""
Google Docs CLI tool for AI Agent automation.
All output is structured JSON: {"status": "success|error", "message": "...", "data": {...}}

Usage:
    python scripts/docs.py create <title> [--content <text>]
    python scripts/docs.py find <query> [--limit <n>]
    python scripts/docs.py get-text <doc_id>
    python scripts/docs.py append-text <doc_id> <text>
    python scripts/docs.py insert-text <doc_id> <text>
    python scripts/docs.py replace-text <doc_id> <old_text> <new_text>
    python scripts/docs.py delete <doc_id>
"""

import argparse
import json
import os
import sys

from googleapiclient.errors import HttpError

# Add parent directory to path for auth module
sys.path.insert(0, os.path.dirname(__file__))
from auth import build_docs_service, build_drive_service

DEFAULT_CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")


def out(status: str, message: str, data: dict = None):
    """Print structured JSON output and exit."""
    result = {"status": status, "message": message}
    if data:
        result["data"] = data
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if status == "error":
        sys.exit(1)


def cmd_create(args):
    """Create a new Google Doc."""
    try:
        docs = build_docs_service(args.credentials)
        body = {"title": args.title}
        doc = docs.documents().create(body=body).execute()
        doc_id = doc["documentId"]

        if args.content:
            requests = [{"insertText": {"location": {"index": 1}, "text": args.content}}]
            docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

        out("success", f"Document '{args.title}' created", {
            "doc_id": doc_id,
            "title": args.title,
            "url": f"https://docs.google.com/document/d/{doc_id}/edit"
        })
    except HttpError as e:
        out("error", f"Failed to create document: {e}")


def cmd_find(args):
    """Search for Google Docs by title."""
    try:
        drive = build_drive_service(args.credentials)
        query = f"mimeType='application/vnd.google-apps.document' and name contains '{args.query}' and trashed=false"
        result = drive.files().list(
            q=query,
            pageSize=args.limit,
            fields="files(id, name, modifiedTime, webViewLink)"
        ).execute()
        files = result.get("files", [])
        out("success", f"Found {len(files)} document(s)", {"documents": files})
    except HttpError as e:
        out("error", f"Search failed: {e}")


def cmd_get_text(args):
    """Get the full text content of a Google Doc."""
    try:
        docs = build_docs_service(args.credentials)
        doc = docs.documents().get(documentId=args.doc_id).execute()
        title = doc.get("title", "")

        # Extract plain text from document body
        text_parts = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if paragraph:
                for pe in paragraph.get("elements", []):
                    text_run = pe.get("textRun")
                    if text_run:
                        text_parts.append(text_run.get("content", ""))

        full_text = "".join(text_parts)
        out("success", f"Retrieved document '{title}'", {
            "doc_id": args.doc_id,
            "title": title,
            "text": full_text,
            "char_count": len(full_text)
        })
    except HttpError as e:
        out("error", f"Failed to get document: {e}")


def cmd_append_text(args):
    """Append text to the end of a Google Doc."""
    try:
        docs = build_docs_service(args.credentials)
        doc = docs.documents().get(documentId=args.doc_id).execute()

        # Find end index of document body
        content = doc.get("body", {}).get("content", [])
        end_index = content[-1].get("endIndex", 1) - 1 if content else 1

        requests = [{"insertText": {"location": {"index": end_index}, "text": args.text}}]
        docs.documents().batchUpdate(documentId=args.doc_id, body={"requests": requests}).execute()
        out("success", "Text appended successfully", {"doc_id": args.doc_id})
    except HttpError as e:
        out("error", f"Failed to append text: {e}")


def cmd_insert_text(args):
    """Insert text at the beginning of a Google Doc."""
    try:
        docs = build_docs_service(args.credentials)
        requests = [{"insertText": {"location": {"index": 1}, "text": args.text}}]
        docs.documents().batchUpdate(documentId=args.doc_id, body={"requests": requests}).execute()
        out("success", "Text inserted at beginning", {"doc_id": args.doc_id})
    except HttpError as e:
        out("error", f"Failed to insert text: {e}")


def cmd_replace_text(args):
    """Find and replace text in a Google Doc."""
    try:
        docs = build_docs_service(args.credentials)
        requests = [{
            "replaceAllText": {
                "containsText": {"text": args.old_text, "matchCase": True},
                "replaceText": args.new_text
            }
        }]
        result = docs.documents().batchUpdate(documentId=args.doc_id, body={"requests": requests}).execute()
        replies = result.get("replies", [{}])
        occurrences = replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
        out("success", f"Replaced {occurrences} occurrence(s)", {
            "doc_id": args.doc_id,
            "occurrences_changed": occurrences
        })
    except HttpError as e:
        out("error", f"Failed to replace text: {e}")


def cmd_delete(args):
    """Move a Google Doc to trash (or permanently delete)."""
    try:
        drive = build_drive_service(args.credentials)
        if args.permanent:
            drive.files().delete(fileId=args.doc_id).execute()
            out("success", "Document permanently deleted", {"doc_id": args.doc_id})
        else:
            drive.files().update(fileId=args.doc_id, body={"trashed": True}).execute()
            out("success", "Document moved to trash", {"doc_id": args.doc_id})
    except HttpError as e:
        out("error", f"Failed to delete document: {e}")


def main():
    parser = argparse.ArgumentParser(description="Google Docs CLI for AI Agent automation")
    parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH)
    subparsers = parser.add_subparsers(dest="command")

    # create
    p = subparsers.add_parser("create", help="Create a new Google Doc")
    p.add_argument("title", help="Document title")
    p.add_argument("--content", default="", help="Initial text content")

    # find
    p = subparsers.add_parser("find", help="Search docs by title")
    p.add_argument("query", help="Search query")
    p.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # get-text
    p = subparsers.add_parser("get-text", help="Get document text content")
    p.add_argument("doc_id", help="Document ID")

    # append-text
    p = subparsers.add_parser("append-text", help="Append text to end of document")
    p.add_argument("doc_id", help="Document ID")
    p.add_argument("text", help="Text to append")

    # insert-text
    p = subparsers.add_parser("insert-text", help="Insert text at beginning of document")
    p.add_argument("doc_id", help="Document ID")
    p.add_argument("text", help="Text to insert")

    # replace-text
    p = subparsers.add_parser("replace-text", help="Find and replace text in document")
    p.add_argument("doc_id", help="Document ID")
    p.add_argument("old_text", help="Text to find")
    p.add_argument("new_text", help="Replacement text")

    # delete
    p = subparsers.add_parser("delete", help="Delete a document (trash by default)")
    p.add_argument("doc_id", help="Document ID")
    p.add_argument("--permanent", action="store_true", help="Permanently delete (skip trash)")

    dispatch = {
        "create": cmd_create,
        "find": cmd_find,
        "get-text": cmd_get_text,
        "append-text": cmd_append_text,
        "insert-text": cmd_insert_text,
        "replace-text": cmd_replace_text,
        "delete": cmd_delete,
    }

    args = parser.parse_args()
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
