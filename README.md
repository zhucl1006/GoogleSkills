# Google Skills

A collection of Google service skills for AI agents (Claude Code, Cursor, Codex, etc.).
Each subdirectory is an independently installable skill.

## Skills

| Skill | Description | Version |
|-------|-------------|---------|
| [google-drive-manager](./google-drive-manager/) | Upload, search, download, update, and delete files in Google Drive | v1.0.0 |
| [google-docs-manager](./google-docs-manager/) | Create, search, read, edit, and delete Google Docs | v1.0.0 |

## Installation

### Option 1 — npx (recommended)

```bash
npx skills add https://github.com/zhucl1006/GoogleSkills.git
```

To install a specific skill only:

```bash
npx skills add https://github.com/zhucl1006/GoogleSkills.git --skill google-drive-manager
npx skills add https://github.com/zhucl1006/GoogleSkills.git --skill google-docs-manager
```

### Option 2 — Manual

Clone and copy the skill directory into your agent's skills folder:

```bash
# Claude Code
git clone https://github.com/zhucl1006/GoogleSkills.git
cp -r GoogleSkills/google-drive-manager ~/.claude/skills/
cp -r GoogleSkills/google-docs-manager ~/.claude/skills/

# Codex / other agents
cp -r GoogleSkills/google-drive-manager ~/.agents/skills/
cp -r GoogleSkills/google-docs-manager ~/.agents/skills/
```

---

## google-drive-manager

Enables AI agents to autonomously manage files in Google Drive using a Service Account.

### Prerequisites

1. **Python dependencies**

   ```bash
   pip install -r google-drive-manager/requirements.txt
   ```

2. **Google Cloud Service Account credentials**

   - Go to [Google Cloud Console](https://console.cloud.google.com/) → IAM & Admin → Service Accounts
   - Create a service account and download the JSON key as `credentials.json`
   - Enable the **Google Drive API** for your project
   - Share the target Drive folder with the service account email (e.g. `my-agent@project.iam.gserviceaccount.com`)

3. **Set credentials path** (optional, defaults to `./credentials.json`)

   ```bash
   export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   ```

4. **Validate setup**

   ```bash
   python google-drive-manager/scripts/auth.py validate
   ```

### Usage

All commands output structured JSON: `{"status": "success/error", "message": "...", "data": {...}}`

```bash
cd google-drive-manager

# Search files
python scripts/drive.py search "quarterly report"
python scripts/drive.py search "report" --limit 5

# Upload
python scripts/drive.py upload ./report.pdf
python scripts/drive.py upload ./report.pdf --name "Q4 Report.pdf" --folder FOLDER_ID

# Download (requires file_id from search)
python scripts/drive.py download FILE_ID ./downloads/report.pdf

# Update / overwrite existing file
python scripts/drive.py update FILE_ID ./report_v2.pdf

# Delete (moves to trash by default)
python scripts/drive.py delete FILE_ID
python scripts/drive.py delete FILE_ID --permanent   # irreversible

# List folder contents
python scripts/drive.py list
python scripts/drive.py list FOLDER_ID --limit 20
```

### How the AI agent uses this skill

When the skill is loaded, the agent follows these rules automatically:

- **Search before operate** — for download/update/delete, the agent always calls `search` first to resolve the `file_id`. It never guesses IDs.
- **Path validation** — before upload/update, the agent confirms the local file exists.
- **Safe delete** — `delete` moves to trash by default; `--permanent` is only used when the user explicitly says "permanently delete".
- **Error self-correction** — on `"status": "error"`, the agent reads the `message` and retries with adjusted parameters.

**Example agent interaction:**

> User: "Help me update the report.txt on Drive"

The agent will automatically chain:
1. `python scripts/drive.py search "report.txt"` → get `file_id`
2. `python scripts/drive.py update <file_id> ./report.txt` → overwrite

### Project Structure

```
google-drive-manager/
  SKILL.md              # Skill definition loaded by the AI agent
  requirements.txt      # Python dependencies
  scripts/
    auth.py             # Credential management (status / validate)
    drive.py            # All Drive operations CLI
```

---

## google-docs-manager

Enables AI agents to autonomously create and manage Google Docs using a Service Account.

### Prerequisites

1. **Python dependencies**

   ```bash
   pip install -r google-docs-manager/requirements.txt
   ```

2. **Google Cloud Service Account credentials**

   - Enable **Google Docs API** and **Google Drive API** for your project
   - Create a service account and download the JSON key as `credentials.json`
   - Share target Drive folders with the service account email

3. **Set credentials path** (optional, defaults to `./credentials.json`)

   ```bash
   export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   ```

4. **Validate setup**

   ```bash
   python google-docs-manager/scripts/auth.py validate
   ```

### Usage

All commands output structured JSON: `{"status": "success/error", "message": "...", "data": {...}}`

```bash
cd google-docs-manager

# Create a new document
python scripts/docs.py create "Meeting Notes"
python scripts/docs.py create "Report" --content "Initial content here"

# Find documents by title
python scripts/docs.py find "meeting notes"
python scripts/docs.py find "report" --limit 5

# Read document content
python scripts/docs.py get-text DOC_ID

# Edit document
python scripts/docs.py append-text DOC_ID "New paragraph at the end"
python scripts/docs.py insert-text DOC_ID "Prepended text"
python scripts/docs.py replace-text DOC_ID "old phrase" "new phrase"

# Delete (moves to trash by default)
python scripts/docs.py delete DOC_ID
python scripts/docs.py delete DOC_ID --permanent   # irreversible
```

### How the AI agent uses this skill

- **Find before edit** — the agent always calls `find` to resolve `doc_id` before editing. It never guesses IDs.
- **Read before replace** — the agent calls `get-text` to understand current content before targeted edits.
- **Safe delete** — `delete` moves to trash by default; `--permanent` only when explicitly requested.

**Example agent interaction:**

> User: "Add a summary section to the Q4 report doc"

The agent will automatically chain:
1. `python scripts/docs.py find "Q4 report"` → get `doc_id`
2. `python scripts/docs.py get-text <doc_id>` → read current content
3. `python scripts/docs.py append-text <doc_id> "## Summary\n..."` → add section

### Project Structure

```
google-docs-manager/
  SKILL.md              # Skill definition loaded by the AI agent
  requirements.txt      # Python dependencies
  scripts/
    auth.py             # Credential management (status / validate)
    docs.py             # All Docs operations CLI
```

---

## Contributing

To add a new Google service skill:

1. Create a new directory (e.g. `google-sheets-manager/`)
2. Follow the structure: `SKILL.md` + `requirements.txt` + `scripts/`
3. Package and validate:
   ```bash
   python3 ~/.claude/skills/skill-creator/scripts/package_skill.py <skill-dir> ./dist
   ```
4. Update this README's skill table
