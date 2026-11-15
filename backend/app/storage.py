import uuid
from pathlib import Path
from app.config import settings

UPLOAD_DIR = Path(settings.upload_dir)

def save_file(data: bytes, extension : str) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    key = f"{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIR/key).write_bytes(data)
    return key

def get_path(key: str) -> Path:
    return UPLOAD_DIR / key

def delete_file(key : str) -> None:
    (UPLOAD_DIR / key).unlink(missing_ok=True)