---
name: google-drive-manager
description: Use when an AI agent needs to interact with Google Drive files. Triggers when user says "backup to cloud", "find file in Drive", "download from Drive", "update cloud file", or "delete from Drive". Requires Google Cloud Service Account credentials.
---

# Google Drive Manager

## Overview

Enables AI agents to autonomously manage Google Drive files using Service Account authentication.
Core rule: **search first to get `file_id`** before any update/download/delete operation.

## When to Use

- User says: "upload/backup to cloud", "find file in Drive", "download from Drive", "update cloud file", "delete from Drive"
- Agent needs `file_id` for download / update / delete
- **Not for** downloading native Google Docs/Sheets (export first)

## Setup

```bash
pip install -r requirements.txt
```

Place `credentials.json` (Google Cloud Service Account key) in the working directory,
or set `GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json`.

Validate credentials:
```bash
python scripts/auth.py validate
```

## AI Agent Rules

**Search-before-operate:** For download/update/delete, ALWAYS call `search` first to get exact `file_id`. Never guess IDs.

**Path validation:** Before `upload` or `update`, confirm `local_path` exists.

**Error self-correction:** On `"status": "error"`, read `message` and retry with adjusted params.

**Safety default:** `delete` moves to trash by default. Only use `--permanent` when user explicitly says "permanently delete".

## Quick Reference

| Operation | Command | Required Args | Trigger Words |
|-----------|---------|---------------|---------------|
| Upload | `upload` | local_path | backup, upload, save to cloud |
| Search | `search` | query | find, list, search Drive |
| Download | `download` | file_id, local_path | download, get from Drive |
| Update | `update` | file_id, local_path | update, modify, overwrite |
| Delete | `delete` | file_id | delete, remove, trash |
| List | `list` | [folder_id] | list folder, show contents |

## Chained Operation Pattern

```bash
# User: "Update report.txt on Drive"
python scripts/drive.py search "report.txt"
# → get file_id from result
python scripts/drive.py update <file_id> ./report.txt
```

## Usage Examples

```bash
# Check auth
python scripts/auth.py status
python scripts/auth.py validate

# Upload
python scripts/drive.py upload ./report.pdf --name "Q4 Report.pdf" --folder FOLDER_ID

# Search
python scripts/drive.py search "quarterly report" --limit 5

# Download
python scripts/drive.py download FILE_ID ./downloads/report.pdf

# Update (overwrite)
python scripts/drive.py update FILE_ID ./report_v2.pdf

# Delete (trash)
python scripts/drive.py delete FILE_ID

# Delete permanently
python scripts/drive.py delete FILE_ID --permanent

# List folder
python scripts/drive.py list FOLDER_ID --limit 20
```

All commands output structured JSON:
```json
{"status": "success", "message": "...", "data": {...}}
{"status": "error",   "message": "..."}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Guessing file_id | Always call `search` first |
| Uploading non-existent file | Check path before calling |
| Permanent delete by default | Keep `--permanent` off unless explicitly asked |
| Downloading Google Docs natively | Export to PDF/CSV first |
