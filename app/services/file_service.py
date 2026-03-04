import hashlib
import os
from pathlib import Path

from fastapi import UploadFile

from ..config import settings


MAGIC_BYTES = {b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF8", b"RIFF", b"BM"}


def sanitize_filename(filename: str) -> str:
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in filename).strip()
    return safe_name or "upload"


async def write_upload_to_temp(upload: UploadFile, upload_dir: Path, safe_name: str, original_name: str) -> tuple[Path, str]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f".tmp_batch_{os.urandom(8).hex()}_{safe_name}"
    total_bytes = 0
    sha256 = hashlib.sha256()

    with temp_path.open("wb") as f:
        while True:
            chunk = await upload.read(settings.upload_chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > settings.max_upload_bytes:
                limit_mb = settings.max_upload_bytes // (1024 * 1024)
                raise ValueError(f"File '{original_name}' exceeds {limit_mb}MB.")
            sha256.update(chunk)
            f.write(chunk)

    if total_bytes == 0:
        raise ValueError(f"File '{original_name}' is empty.")

    return temp_path, sha256.hexdigest()


def validate_image_magic(temp_path: Path, original_name: str) -> None:
    with temp_path.open("rb") as f:
        header = f.read(16)
    if not any(header.startswith(magic) for magic in MAGIC_BYTES):
        raise ValueError(f"'{original_name}' is not a valid image.")


def finalize_upload(temp_path: Path, upload_dir: Path, file_hash: str, safe_name: str) -> Path:
    final_path = upload_dir / f"{file_hash[:16]}_{safe_name}"
    temp_path.replace(final_path)
    return final_path


def safe_unlink(path: Path) -> None:
    path.unlink(missing_ok=True)


def is_within_upload_dir(path: Path, upload_root: Path) -> bool:
    return upload_root in path.resolve().parents

