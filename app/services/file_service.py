import hashlib
import os
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from ..config import settings


ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".avif",
}

MAGIC_SIGS = [
    (0, b"\xff\xd8\xff"),
    (0, b"\x89PNG\r\n\x1a\n"),
    (0, b"GIF8"),
    (0, b"RIFF"),
    (0, b"BM"),
    (4, b"ftyp"),
]


def sanitize_filename(filename: str) -> str:
    parsed_name = Path(filename).name
    stem = Path(parsed_name).stem
    ext = Path(parsed_name).suffix.lower()

    safe_stem = "".join(ch for ch in stem if ch.isalnum() or ch in ("-", "_"))[:128]
    if not safe_stem:
        safe_stem = "upload"

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = ".png"

    return f"{safe_stem}{ext}"


async def write_upload_to_temp(upload: UploadFile, upload_dir: Path, safe_name: str, original_name: str) -> tuple[Path, str]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f".tmp_batch_{os.urandom(8).hex()}_{safe_name}"
    total_bytes = 0
    sha256 = hashlib.sha256()

    async with aiofiles.open(temp_path, "wb") as f:
        while True:
            chunk = await upload.read(settings.upload_chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > settings.max_upload_bytes:
                limit_mb = settings.max_upload_bytes // (1024 * 1024)
                raise ValueError(f"File '{original_name}' exceeds {limit_mb}MB.")
            sha256.update(chunk)
            await f.write(chunk)

    if total_bytes == 0:
        raise ValueError(f"File '{original_name}' is empty.")

    return temp_path, sha256.hexdigest()


def validate_image_magic(temp_path: Path, original_name: str) -> None:
    with temp_path.open("rb") as f:
        header = f.read(12)
        is_valid = any(
            header[offset:offset + len(signature)] == signature
            for offset, signature in MAGIC_SIGS
        )
        f.seek(0)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{original_name}' is not a valid image.",
        )


def finalize_upload(temp_path: Path, upload_dir: Path, file_hash: str, safe_name: str) -> Path:
    final_path = upload_dir / f"{file_hash[:16]}_{safe_name}"
    temp_path.replace(final_path)
    return final_path


def safe_unlink(path: Path) -> None:
    path.unlink(missing_ok=True)


def is_within_upload_dir(path: Path, upload_root: Path) -> bool:
    return upload_root in path.resolve().parents
