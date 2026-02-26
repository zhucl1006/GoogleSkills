# Google Skills

Claude Code 的 Google 服务技能集合，每个子目录是一个独立的可分发技能。

## 技能列表

| 技能 | 描述 | 状态 |
|------|------|------|
| [google-drive-manager](./google-drive-manager/) | Google Drive 文件管理（上传/搜索/下载/更新/删除） | ✅ v1.0.0 |

## 目录结构

```
googleskills/
  google-drive-manager/     # Google Drive 文件管理技能
    SKILL.md                # 技能文档与守则
    google_drive_skill.py   # Python 实现
  dist/                     # 打包输出目录
    google-drive-manager.zip
```

## 安装技能

将对应技能目录复制到 `~/.claude/skills/` 即可：

```bash
cp -r google-drive-manager ~/.claude/skills/
```

## 打包分发

```bash
python3 ~/.claude/skills/skill-creator/scripts/package_skill.py <skill-dir> ./dist
```

## 依赖

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

需要 Google Cloud Service Account 的 `credentials.json` 文件。
