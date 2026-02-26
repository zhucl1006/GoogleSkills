import os
import io
from typing import Dict, Any, Optional

# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError


class GoogleDriveSkill:
    """
    Google Drive API 封装，专为 AI Agent 设计。
    提供文件上传、下载、搜索、更新与删除的原子化操作。
    """

    def __init__(self, credentials_path: str):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.credentials_path = credentials_path
        self.service = self._authenticate()

    def _authenticate(self):
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"找不到凭证文件: {self.credentials_path}")
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )
        return build('drive', 'v3', credentials=creds)

    def upload_file(
        self,
        local_file_path: str,
        custom_file_name: Optional[str] = None,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """上传本地文件到 Google Drive。"""
        if not os.path.exists(local_file_path):
            return {"status": "error", "message": f"本地文件不存在: {local_file_path}"}

        file_name = custom_file_name or os.path.basename(local_file_path)
        file_metadata = {'name': file_name}
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        try:
            media = MediaFileUpload(local_file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata, media_body=media, fields='id, webViewLink, name'
            ).execute()
            return {
                "status": "success",
                "message": f"文件 '{file_name}' 上传成功。",
                "data": {
                    "file_id": file.get('id'),
                    "file_name": file.get('name'),
                    "web_view_link": file.get('webViewLink')
                }
            }
        except HttpError as e:
            return {"status": "error", "message": f"上传失败: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"未知错误: {e}"}

    def search_files(self, query_string: str) -> Dict[str, Any]:
        """搜索 Google Drive 中的文件（过滤已删除）。"""
        drive_query = f"name contains '{query_string}' and trashed = false"
        try:
            results = self.service.files().list(
                q=drive_query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, webViewLink)',
                pageSize=10
            ).execute()
            items = results.get('files', [])
            return {
                "status": "success",
                "message": f"找到 {len(items)} 个符合的文件。",
                "data": items
            }
        except HttpError as e:
            return {"status": "error", "message": f"搜索失败: {e}"}

    def download_file(self, file_id: str, local_save_path: str) -> Dict[str, Any]:
        """从 Google Drive 下载文件到本地（不支持直接下载 Google Docs/Sheets）。"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(local_save_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
            return {
                "status": "success",
                "message": f"文件已下载至 {local_save_path}",
                "data": {"local_path": local_save_path}
            }
        except HttpError as e:
            return {"status": "error", "message": f"下载失败: {e}"}

    def update_file(self, file_id: str, local_file_path: str) -> Dict[str, Any]:
        """用��地文件内容覆写 Google Drive 上的现有文件。"""
        if not os.path.exists(local_file_path):
            return {"status": "error", "message": f"本地文件不存在: {local_file_path}"}
        try:
            media = MediaFileUpload(local_file_path, resumable=True)
            file = self.service.files().update(
                fileId=file_id, media_body=media, fields='id, webViewLink, name'
            ).execute()
            return {
                "status": "success",
                "message": f"文件 '{file.get('name')}' 更新成功。",
                "data": {
                    "file_id": file.get('id'),
                    "file_name": file.get('name'),
                    "web_view_link": file.get('webViewLink')
                }
            }
        except HttpError as e:
            return {"status": "error", "message": f"更新失败: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"未知错误: {e}"}

    def delete_file(self, file_id: str, permanent: bool = False) -> Dict[str, Any]:
        """删除文件。默认移至垃圾桶，permanent=True 才永久删除。"""
        try:
            if permanent:
                self.service.files().delete(fileId=file_id).execute()
                action_msg = "已永久删除"
            else:
                self.service.files().update(fileId=file_id, body={'trashed': True}).execute()
                action_msg = "已移至垃圾桶"
            return {"status": "success", "message": f"文件 (ID: {file_id}) {action_msg}。"}
        except HttpError as e:
            return {"status": "error", "message": f"删除失败: {e}"}


if __name__ == "__main__":
    try:
        drive = GoogleDriveSkill("credentials.json")
        print("Google Drive Skill 初始化成功！")
        # result = drive.search_files("report")
        # print(result)
    except Exception as e:
        print(f"初始化失败: {e}")
        print("请确认 credentials.json 是否存在且有效。")
