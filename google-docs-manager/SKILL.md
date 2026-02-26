---
name: google-docs-manager
description: Use when an AI agent needs to interact with Google Docs. Triggers when user says "create a doc", "find document", "read doc content", "append to doc", "replace text in doc", or "delete document". Requires Google Cloud Service Account credentials.
---

# Google Docs Manager

Manage Google Docs via Service Account — no browser interaction required, fully automatable.

## Prerequisites

1. Google Cloud project with Docs API + Drive API enabled
2. Service Account JSON key file
3. Set `GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json`
4. Install: `pip install -r requirements.txt`

## When to Use

- User says: "create a doc", "write a document", "find doc", "read doc content", "append/insert/replace text in doc", "delete document"
- Agent needs to read or modify Google Docs content programmatically
- **Not for** downloading binary files or managing non-Doc files (use google-drive-manager instead)

## Quick Reference

| Task | Command |
|------|---------|
| Create doc | `python scripts/docs.py create "Title" [--content "text"]` |
| Find docs | `python scripts/docs.py find "query" [--limit 10]` |
| Read content | `python scripts/docs.py get-text <doc_id>` |
| Append text | `python scripts/docs.py append-text <doc_id> "text"` |
| Insert at start | `python scripts/docs.py insert-text <doc_id> "text"` |
| Find & replace | `python scripts/docs.py replace-text <doc_id> "old" "new"` |
| Delete (trash) | `python scripts/docs.py delete <doc_id>` |
| Delete (permanent) | `python scripts/docs.py delete <doc_id> --permanent` |

## Output Format

All commands return structured JSON:

```json
{"status": "success", "message": "...", "data": {...}}
{"status": "error",   "message": "..."}
```

## Agent Rules

1. Always check `status` field before using `data`
2. Use `find` before editing — never guess doc IDs
3. Use `get-text` to read content before making targeted edits
4. Prefer `replace-text` for targeted changes; use `append-text` for additions
5. Default `delete` moves to trash — use `--permanent` only when explicitly requested
6. `doc_id` is the alphanumeric string in the Google Docs URL: `https://docs.google.com/document/d/<doc_id>/edit`

## Chained Operation Pattern

```bash
# Find → read → edit workflow
python scripts/docs.py find "meeting notes"
# → extract doc_id from data.documents[0].id

python scripts/docs.py get-text <doc_id>
# → read current content

python scripts/docs.py replace-text <doc_id> "old section" "updated section"
# → targeted edit
```

## Auth Management

```bash
python scripts/auth.py status      # Check credentials file
python scripts/auth.py validate    # Test API connectivity
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Guessing doc_id | Always call `find` first to get exact `doc_id` |
| Editing without reading | Call `get-text` before `replace-text` to confirm content exists |
| Permanent delete by default | Keep `--permanent` off unless user explicitly says so |
| Using doc URL as doc_id | Extract only the alphanumeric ID from the URL, not the full URL |
| Appending when replace is needed | Use `replace-text` for targeted edits, `append-text` only for additions |
