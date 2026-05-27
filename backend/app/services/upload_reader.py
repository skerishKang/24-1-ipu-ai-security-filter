from __future__ import annotations

from typing import Any

DEFAULT_UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


async def read_limited_upload(
    file: Any,
    max_bytes: int,
    *,
    chunk_size: int = DEFAULT_UPLOAD_READ_CHUNK_SIZE,
    error_factory: Any = None,
) -> bytes:
    """Read upload file stream in chunks, raising an error immediately if max_bytes is exceeded."""
    chunks: list[bytes] = []
    total_size = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break

        total_size += len(chunk)
        if total_size > max_bytes:
            if error_factory:
                raise error_factory()
            raise ValueError(f"파일 크기는 최대 {max_bytes} bytes를 초과할 수 없습니다.")

        chunks.append(chunk)

    return b"".join(chunks)
