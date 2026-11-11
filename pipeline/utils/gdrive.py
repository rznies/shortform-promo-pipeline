"""
Google Drive integration helpers using gdrive CLI or REST API.
"""

import json
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional

GDRIVE_BIN = shutil.which("gdrive") or shutil.which("gdrive.cmd") or "gdrive"


def extract_id_from_url(url_or_id: str) -> str:
    """Extract folder or file ID from a Google Drive URL or raw ID string."""
    if not url_or_id:
        return ""
    # Matches /folders/<id> or /d/<id>
    match = re.search(r"/(?:folders|d)/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    # Check query param ?id=<id>
    match_q = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url_or_id)
    if match_q:
        return match_q.group(1)
    # Raw ID
    return url_or_id.strip()


def list_folder_contents(folder_id: str) -> List[Dict[str, str]]:
    """List all files and subfolders inside a Google Drive folder using gdrive CLI."""
    clean_id = extract_id_from_url(folder_id)
    cmd = [GDRIVE_BIN, "readonly", "ls", clean_id, "--json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=(os.name == "nt"))
        return json.loads(res.stdout)
    except Exception as e:
        print(f"[gdrive] Error listing folder {clean_id}: {e}")
        return []


def download_file(file_id: str, dest_path: str) -> bool:
    """Download a file from Google Drive to local disk."""
    clean_id = extract_id_from_url(file_id)
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    cmd = [GDRIVE_BIN, "readonly", "download", clean_id, "--out", dest_path]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, shell=(os.name == "nt"))
        return True
    except subprocess.CalledProcessError as e:
        print(f"[gdrive] Failed to download {clean_id}: {e.stderr}")
        return False


def upload_file(local_path: str, parent_folder_id: str) -> Optional[str]:
    """Upload a file to Google Drive and return the new file ID."""
    clean_parent = extract_id_from_url(parent_folder_id)
    if not os.path.exists(local_path):
        print(f"[gdrive] File not found for upload: {local_path}")
        return None
    cmd = [GDRIVE_BIN, "mutate", "upload", local_path, "--parent", clean_parent]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=(os.name == "nt"))
        match = re.search(r"Uploaded ([a-zA-Z0-9_-]+)", res.stdout)
        return match.group(1) if match else "uploaded"
    except subprocess.CalledProcessError as e:
        print(f"[gdrive] Upload error for {local_path}: {e.stderr}")
        return None
