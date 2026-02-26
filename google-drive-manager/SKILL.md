---
name: google-drive-manager
description: Use when an AI agent needs to manage files in Google Drive - uploading, searching, downloading, updating, or deleting files. Triggers on user instructions like "backup to cloud", "find file in Drive", "update cloud file", "download from Drive", or "delete from Drive". Requires Google Cloud Service Account credentials.
---

# Google Drive Manager

## Overview

赋予 AI 代理自主管理 Google Drive 文件的能力。核心规则：**操作前必须先搜索**，通过 `search_files` 获取精确 `file_id`，绝不猜测 ID。

## When to Use

- 用户说：「上传/备份到云端」、「在 Drive 找文件」、「下载 Drive 文件」、「更新云端文件」、「删除 Drive 文件」
- 需要 file_id 才能执行 download / update / delete
- **不适用于**直接下载 Google Docs/Sheets 原生格式（需先导出）

## AI 代理守则

**先搜索，后操作：** download/update/delete 前，必须先调用 `search_files` 获取 `file_id`，绝不猜测。

**路径验证：** `upload_file` / `update_file` 前确认 `local_file_path` 存在。

**错误自修正：** 收到 `{"status": "error"}` 时，读取 `message` 字段并尝试调整参数重试。

**安全默认：** `delete_file` 的 `permanent` 默认为 `false`（移至垃圾桶），除非用户明确说「永久删除」。

## Quick Reference

| 操作 | 工具 | 必填参数 | 触发词 |
|------|------|----------|--------|
| 上传 | `upload_file` | local_file_path | 备份、上传、保存到云端 |
| 搜索 | `search_files` | query_string | 找、列出、查询 Drive |
| 下载 | `download_file` | file_id, local_save_path | 下载、获取 |
| 更新 | `update_file` | file_id, local_file_path | 更新、修改、覆写 |
| 删除 | `delete_file` | file_id | 删除、移除、清除 |

## 串联操作模式

```python
# 用户: "帮我更新云端上的 report.txt"
result = drive.search_files("report.txt")   # Step 1: 获取 file_id
file_id = result["data"][0]["id"]
drive.update_file(file_id, "/local/report.txt")  # Step 2: 更新内容
```

## Setup

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

需要 `credentials.json`（Google Cloud Service Account JSON 密钥文件）。

## Implementation

完整实现见 `google_drive_skill.py`。

```python
from google_drive_skill import GoogleDriveSkill

drive = GoogleDriveSkill("credentials.json")

# 搜索文件
result = drive.search_files("report")
# → {"status": "success", "data": [{"id": "...", "name": "report.txt", ...}]}

# 上传文件
drive.upload_file("/local/data.csv", custom_file_name="backup_data.csv")
```

## Common Mistakes

| 错误 | 修正 |
|------|------|
| 猜测 file_id | 先调用 search_files |
| 上传不存在的本地文件 | 检查路径后再调用 |
| 默认永久删除 | 保持 permanent=False |
| 直接下载 Google Docs | 先导出为 PDF/CSV 再下载 |
