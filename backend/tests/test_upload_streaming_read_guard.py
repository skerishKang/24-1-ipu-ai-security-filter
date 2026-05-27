"""Tests for streaming upload read guard limit enforcement."""

from __future__ import annotations

import unittest

from app.core.exceptions import FileTooLargeError
from app.services.audio_transcriber import BaseAudioTranscriber
from app.services.file_parser import TextFileParser
from app.services.upload_reader import read_limited_upload


class FakeUploadFile:
    """Fake UploadFile that tracks read offset and read count."""

    def __init__(self, content: bytes, filename: str = "test.txt", content_type: str = "text/plain"):
        self.content = content
        self.offset = 0
        self.read_count = 0
        self.filename = filename
        self.content_type = content_type
        self.size = None  # metadata size is None to force body reading

    async def read(self, size: int = -1) -> bytes:
        self.read_count += 1
        if self.offset >= len(self.content):
            return b""

        if size < 0:
            chunk = self.content[self.offset :]
            self.offset = len(self.content)
            return chunk

        chunk = self.content[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


class StreamingReadGuardHelperTest(unittest.IsolatedAsyncioTestCase):
    async def test_read_under_limit_success(self):
        content = b"hello world" * 10  # 110 bytes
        file = FakeUploadFile(content)

        result = await read_limited_upload(file, 200, chunk_size=20)
        self.assertEqual(result, content)
        self.assertEqual(file.read_count, 7)  # 6 chunks of 20 + 1 empty read

    async def test_read_over_limit_raises_and_stops_early(self):
        content = b"a" * 100  # 100 bytes
        file = FakeUploadFile(content)

        with self.assertRaises(ValueError) as ctx:
            await read_limited_upload(file, 30, chunk_size=10)

        self.assertEqual(str(ctx.exception), "파일 크기는 최대 30 bytes를 초과할 수 없습니다.")
        # Stops immediately after reading 4th chunk (40 bytes > 30 max_bytes)
        self.assertEqual(file.read_count, 4)


class StreamingReadGuardParserTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_parser_stops_reading_early_on_huge_file(self):
        parser = TextFileParser(max_upload_bytes=2 * 1024 * 1024)
        content = b"x" * (5 * 1024 * 1024)
        file = FakeUploadFile(content, filename="test.txt", content_type="text/plain")

        with self.assertRaises(FileTooLargeError):
            await parser.parse(file)

        # Chunk size is DEFAULT_UPLOAD_READ_CHUNK_SIZE (1MB).
        # It should read exactly 3 chunks (3MB total) and then raise early.
        self.assertEqual(file.read_count, 3)


class StreamingReadGuardAudioTest(unittest.IsolatedAsyncioTestCase):
    async def test_audio_transcriber_stops_reading_early_on_huge_file(self):
        transcriber = BaseAudioTranscriber(max_upload_bytes=2 * 1024 * 1024)
        content = b"x" * (5 * 1024 * 1024)
        file = FakeUploadFile(content, filename="test.wav", content_type="audio/wav")

        with self.assertRaises(ValueError) as ctx:
            await transcriber._read_validated_audio(file)

        self.assertIn("MB 이하 파일만 고려합니다", str(ctx.exception))
        # Chunk size is DEFAULT_UPLOAD_READ_CHUNK_SIZE (1MB).
        # It should read exactly 3 chunks (3MB total) and then raise early.
        self.assertEqual(file.read_count, 3)
