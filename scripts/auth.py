"""沿用既有 google-drive-mcp 的 OAuth 憑證，唯讀取不覆寫原始 token 檔。

refresh 後的最新 token 狀態存在本專案自己的 .credentials/token.json，
不會動到 ~/.config/google-drive-mcp/tokens.json（那是另一個正在跑的 MCP server 在用）。
"""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SOURCE_KEYS_PATH = Path.home() / ".config/google-drive-mcp/gcp-oauth.keys.json"
SOURCE_TOKEN_PATH = Path.home() / ".config/google-drive-mcp/tokens.json"
LOCAL_CACHE_PATH = Path(__file__).resolve().parent.parent / ".credentials" / "token.json"


def get_credentials() -> Credentials:
    LOCAL_CACHE_PATH.parent.mkdir(exist_ok=True)

    if LOCAL_CACHE_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(LOCAL_CACHE_PATH))
    else:
        with open(SOURCE_KEYS_PATH) as f:
            client_info = json.load(f)["installed"]
        with open(SOURCE_TOKEN_PATH) as f:
            token_data = json.load(f)
        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data["refresh_token"],
            token_uri=client_info["token_uri"],
            client_id=client_info["client_id"],
            client_secret=client_info["client_secret"],
            scopes=token_data.get("scope", "").split(),
        )

    if not creds.valid:
        creds.refresh(Request())

    LOCAL_CACHE_PATH.write_text(creds.to_json())
    return creds
