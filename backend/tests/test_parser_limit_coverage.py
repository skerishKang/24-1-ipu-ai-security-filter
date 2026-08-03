from __future__ import annotations

import io
import unittest

from app.core.exceptions import ProcessingLimitExceededError
from app.services.file_parser import DefaultFileParser, ParsedFileContent
from fastapi import UploadFile
from starlette.datastructures import Headers


class ParserLimitCoverageTest(unittest.IsolatedAsyncioTestCase):
    async def test_text_parse_allows_content_at_limit(self) -> None:
        parser = DefaultFileParser(max_extracted_text_chars=5)
        upload = UploadFile(
            filename="sample.txt",
            file=io.BytesIO(b"hello"),
            headers=Headers({"content-type": "text/plain"}),
        )

        parsed = await parser.parse(upload)

        self.assertEqual(parsed.content, "hello")
        self.assertEqual(parsed.normalized_content_type, "text/plain")

    async def test_text_parse_rejects_content_over_limit(self) -> None:
        parser = DefaultFileParser(max_extracted_text_chars=4)
        upload = UploadFile(
            filename="sample.txt",
            file=io.BytesIO(b"hello"),
            headers=Headers({"content-type": "text/plain"}),
        )

        with self.assertRaises(ProcessingLimitExceededError) as ctx:
            await parser.parse(upload)

        self.assertIn("Extracted text length", str(ctx.exception))
        self.assertIn("4", str(ctx.exception))

    async def test_common_limit_allows_parsed_content_at_limit(self) -> None:
        parser = DefaultFileParser(max_extracted_text_chars=4)
        parsed = ParsedFileContent(
            content="abcd",
            normalized_content_type="application/pdf",
            filename="sample.pdf",
        )

        result = parser._enforce_extracted_text_limit(parsed)

        self.assertEqual(result, parsed)

    async def test_common_limit_rejects_parsed_content_over_limit(self) -> None:
        parser = DefaultFileParser(max_extracted_text_chars=4)
        parsed = ParsedFileContent(
            content="abcde",
            normalized_content_type="application/pdf",
            filename="sample.pdf",
        )

        with self.assertRaises(ProcessingLimitExceededError) as ctx:
            parser._enforce_extracted_text_limit(parsed)

        self.assertIn("Extracted text length", str(ctx.exception))
        self.assertIn("4", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
