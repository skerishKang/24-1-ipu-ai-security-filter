from __future__ import annotations

import io
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from app.core.exceptions import ProcessingLimitExceededError
from app.services.file_parser import (
    DefaultFileParser,
    DocxFileParser,
    HwpxFileParser,
    PdfFileParser,
    TextFileParser,
)
from fastapi import UploadFile
from pypdf import PdfWriter
from starlette.datastructures import Headers


class TextFileParserTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_accepts_markdown_file(self) -> None:
        parser = TextFileParser()
        upload = UploadFile(
            filename="sample.md",
            file=io.BytesIO(b"# hello\ncontact@ipu.co.kr"),
            headers=Headers({"content-type": "text/markdown"}),
        )
        upload.size = len(b"# hello\ncontact@ipu.co.kr")

        parsed = await parser.parse(upload)

        self.assertEqual(parsed.filename, "sample.md")
        self.assertEqual(parsed.normalized_content_type, "text/markdown")
        self.assertIn("contact@ipu.co.kr", parsed.content)

    async def test_parse_rejects_unsupported_extension(self) -> None:
        parser = TextFileParser()
        upload = UploadFile(
            filename="sample.pdf",
            file=io.BytesIO(b"fake"),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = 4

        with self.assertRaisesRegex(ValueError, ".txt, .md, .csv, .pdf, .docx, .hwpx"):
            await parser.parse(upload)


class DocxFileParserTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_accepts_docx_file(self) -> None:
        parser = DocxFileParser()
        upload = UploadFile(
            filename="sample.docx",
            file=io.BytesIO(build_docx_bytes(["First paragraph", "contact@ipu.co.kr"])),
            headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertEqual(parsed.filename, "sample.docx")
        self.assertEqual(
            parsed.normalized_content_type,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("First paragraph", parsed.content)
        self.assertIn("contact@ipu.co.kr", parsed.content)

    async def test_parse_rejects_empty_docx_body(self) -> None:
        parser = DocxFileParser()
        upload = UploadFile(
            filename="empty.docx",
            file=io.BytesIO(build_docx_bytes(["   ", ""])),
            headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, "DOCX"):
            await parser.parse(upload)


class PdfFileParserTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_accepts_pdf_file(self) -> None:
        parser = PdfFileParser()
        upload = UploadFile(
            filename="sample.pdf",
            file=io.BytesIO(build_pdf_bytes(["Hello PDF contact@ipu.co.kr"])),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertEqual(parsed.filename, "sample.pdf")
        self.assertEqual(parsed.normalized_content_type, "application/pdf")
        self.assertIn("Hello PDF", parsed.content)
        self.assertIn("contact@ipu.co.kr", parsed.content)

    async def test_default_parser_routes_pdf_to_pdf_parser(self) -> None:
        parser = DefaultFileParser()
        upload = UploadFile(
            filename="sample.pdf",
            file=io.BytesIO(build_pdf_bytes(["Routed PDF"])),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertIn("Routed PDF", parsed.content)

    async def test_default_parser_routes_docx_to_docx_parser(self) -> None:
        parser = DefaultFileParser()
        upload = UploadFile(
            filename="sample.docx",
            file=io.BytesIO(build_docx_bytes(["Routed DOCX"])),
            headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertIn("Routed DOCX", parsed.content)

    async def test_parse_merges_multiple_pdf_pages(self) -> None:
        parser = PdfFileParser()
        upload = UploadFile(
            filename="sample.pdf",
            file=io.BytesIO(build_pdf_bytes(["First page", "Second   page  contact@ipu.co.kr"])),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertIn("First page", parsed.content)
        self.assertIn("Second page contact@ipu.co.kr", parsed.content)

    async def test_parse_rejects_encrypted_pdf(self) -> None:
        parser = PdfFileParser()
        upload = UploadFile(
            filename="locked.pdf",
            file=io.BytesIO(build_encrypted_pdf_bytes()),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, "암호화된 PDF"):
            await parser.parse(upload)

    async def test_parse_falls_back_to_ocr_when_pdf_text_layer_is_empty(self) -> None:
        parser = OcrFallbackPdfFileParser("Scanned contact@ipu.co.kr")
        upload = UploadFile(
            filename="scan.pdf",
            file=io.BytesIO(build_blank_pdf_bytes()),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertIn("Scanned contact@ipu.co.kr", parsed.content)

    async def test_parse_rejects_pdf_when_ocr_also_returns_empty(self) -> None:
        parser = OcrFallbackPdfFileParser("")
        upload = UploadFile(
            filename="scan.pdf",
            file=io.BytesIO(build_blank_pdf_bytes()),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, "텍스트를 추출할 수 있는 PDF"):
            await parser.parse(upload)

    async def test_parse_explains_when_ocr_toolchain_is_missing(self) -> None:
        parser = MissingOcrToolPdfFileParser()
        upload = UploadFile(
            filename="scan.pdf",
            file=io.BytesIO(build_blank_pdf_bytes()),
            headers=Headers({"content-type": "application/pdf"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, "tesseract 와 pdftoppm"):
            await parser.parse(upload)


class HwpxFileParserTest(unittest.IsolatedAsyncioTestCase):
    async def test_parse_accepts_hwpx_file(self) -> None:
        parser = HwpxFileParser()
        upload = UploadFile(
            filename="sample.hwpx",
            file=io.BytesIO(build_hwpx_bytes([["첫 문단", "contact@ipu.co.kr"], ["둘째 문단"]])),
            headers=Headers({"content-type": "application/haansofthwpx"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertEqual(parsed.filename, "sample.hwpx")
        self.assertEqual(parsed.normalized_content_type, "application/haansofthwpx")
        self.assertIn("첫 문단", parsed.content)
        self.assertIn("contact@ipu.co.kr", parsed.content)
        self.assertIn("둘째 문단", parsed.content)

    async def test_default_parser_routes_hwpx_to_hwpx_parser(self) -> None:
        parser = DefaultFileParser()
        upload = UploadFile(
            filename="sample.hwpx",
            file=io.BytesIO(build_hwpx_bytes([["Routed HWPX"]])),
            headers=Headers({"content-type": "application/haansofthwpx"}),
        )
        upload.size = len(upload.file.getvalue())

        parsed = await parser.parse(upload)

        self.assertIn("Routed HWPX", parsed.content)

    async def test_default_parser_rejects_binary_hwp_with_conversion_guidance(self) -> None:
        parser = DefaultFileParser()
        upload = UploadFile(
            filename="sample.hwp",
            file=io.BytesIO(b"fake-hwp"),
            headers=Headers({"content-type": "application/x-hwp"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, ".hwpx, .pdf, .docx, .txt"):
            await parser.parse(upload)

    async def test_parse_rejects_empty_hwpx_body(self) -> None:
        parser = HwpxFileParser()
        upload = UploadFile(
            filename="empty.hwpx",
            file=io.BytesIO(build_hwpx_bytes([["   "]])),
            headers=Headers({"content-type": "application/haansofthwpx"}),
        )
        upload.size = len(upload.file.getvalue())

        with self.assertRaisesRegex(ValueError, "HWPX"):
            await parser.parse(upload)


def build_pdf_bytes(page_texts: list[str]) -> bytes:
    objects = []
    page_references = []

    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    for index, text in enumerate(page_texts):
        page_object_number = 3 + (index * 2)
        content_object_number = page_object_number + 1
        page_references.append(f"{page_object_number} 0 R".encode("ascii"))

        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 120 Td ({escaped}) Tj ET".encode()

        objects.append(
            f"{page_object_number} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents {content_object_number} 0 R /Resources << /Font << /F1 {3 + (len(page_texts) * 2)} 0 R >> >> >>\nendobj\n".encode(
                "ascii"
            )
        )
        objects.append(
            f"{content_object_number} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        )

    objects.insert(
        1,
        b"2 0 obj\n<< /Type /Pages /Kids ["
        + b" ".join(page_references)
        + b"] /Count "
        + str(len(page_texts)).encode("ascii")
        + b" >>\nendobj\n",
    )
    font_object_number = 3 + (len(page_texts) * 2)
    objects.append(
        f"{font_object_number} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode(
            "ascii"
        )
    )

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b""
    offsets = [0]
    current = len(header)
    for obj in objects:
        offsets.append(current)
        body += obj
        current += len(obj)

    xref_offset = len(header) + len(body)
    xref_entries = [b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref_entries.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        b"xref\n0 "
        + str(len(offsets)).encode("ascii")
        + b"\n"
        + b"".join(xref_entries)
        + b"trailer\n<< /Size "
        + str(len(offsets)).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )

    return header + body + trailer


def build_encrypted_pdf_bytes() -> bytes:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=200)
    writer.encrypt("secret")
    writer.write(buffer)
    return buffer.getvalue()


def build_blank_pdf_bytes(page_count: int = 1) -> bytes:
    buffer = io.BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=300, height=200)
    writer.write(buffer)
    return buffer.getvalue()


def build_docx_bytes(paragraphs: list[str]) -> bytes:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{escape_xml(paragraph)}</w:t></w:r></w:p>" for paragraph in paragraphs
    )
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{paragraph_xml}</w:body>
</w:document>
"""

    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
    return buffer.getvalue()


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_hwpx_bytes(sections: list[list[str]]) -> bytes:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", "application/hwp+zip")
        archive.writestr("version.xml", "<?xml version='1.0' encoding='UTF-8'?><version app='manual-preview'/>")
        archive.writestr(
            "Contents/content.hpf",
            "<?xml version='1.0' encoding='UTF-8'?><opf:package xmlns:opf='http://www.idpf.org/2007/opf'/>",
        )
        for index, paragraphs in enumerate(sections):
            para_xml = "".join(
                f"<hp:p id='{1000 + paragraph_index}'><hp:run charPrIDRef='0'><hp:t>{escape_xml(paragraph)}</hp:t></hp:run></hp:p>"
                for paragraph_index, paragraph in enumerate(paragraphs)
            )
            section_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
        xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
  {para_xml}
</hs:sec>
"""
            archive.writestr(f"Contents/section{index}.xml", section_xml)
    return buffer.getvalue()


class OcrFallbackPdfFileParser(PdfFileParser):
    def __init__(self, ocr_text: str) -> None:
        super().__init__()
        self._ocr_text = ocr_text

    def _extract_pdf_via_ocr(self, raw: bytes) -> str:
        return self._ocr_text


class MissingOcrToolPdfFileParser(PdfFileParser):
    def _is_ocr_toolchain_available(self) -> bool:
        return False


class OcrSimulatedPdfFileParser(PdfFileParser):
    """Simulates OCR processing without running external tools."""

    def __init__(self, simulated_page_count: int, ocr_text: str = "mocked") -> None:
        super().__init__()
        self._simulated_page_count = simulated_page_count
        self._ocr_text = ocr_text

    def _is_ocr_toolchain_available(self) -> bool:
        return True

    def _run_command(self, command: list[str], *, capture_output: bool = False, timeout: int | None = None) -> str:
        # Simulate a successful pdftoppm — no-op
        return ""

    def _extract_pdf_via_ocr(self, raw: bytes) -> str:
        from app.services.file_parser import MAX_OCR_PAGES

        if self._simulated_page_count > MAX_OCR_PAGES:
            raise ProcessingLimitExceededError(
                f"OCR page count {self._simulated_page_count} exceeds the processing limit of {MAX_OCR_PAGES} pages."
            )
        # If within limit, simulate extracting text from each page
        return "\n".join([self._ocr_text] * self._simulated_page_count)


class OcrTimeoutPdfFileParser(PdfFileParser):
    """Simulates an OCR toolchain timeout by raising directly."""

    def _is_ocr_toolchain_available(self) -> bool:
        return True

    def _run_command(self, command: list[str], *, capture_output: bool = False, timeout: int | None = None) -> str:
        raise ProcessingLimitExceededError(
            f"OCR command exceeded the processing timeout of {timeout or 15} seconds."
        )

    def _run_tesseract(self, image_path: Path, timeout: int = 15) -> str:
        raise ProcessingLimitExceededError(
            f"OCR command exceeded the processing timeout of {timeout} seconds."
        )


class PdfProcessingGuardrailTest(unittest.IsolatedAsyncioTestCase):
    """Tests for PDF/OCR processing guardrails using mock/monkeypatch only."""

    async def test_pdf_page_limit_exceeded_raises_error(self) -> None:
        """PDF page count > MAX_PDF_PAGES raises ProcessingLimitExceededError."""
        parser = PdfFileParser()

        with patch("app.services.file_parser.MAX_PDF_PAGES", 1):
            upload = UploadFile(
                filename="sample.pdf",
                file=io.BytesIO(build_pdf_bytes(["Page 1", "Page 2"])),
                headers=Headers({"content-type": "application/pdf"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("PDF page count", str(ctx.exception))
            self.assertIn("2", str(ctx.exception))
            self.assertIn("1", str(ctx.exception))

    async def test_pdf_page_limit_within_limit_succeeds(self) -> None:
        """PDF page count <= MAX_PDF_PAGES processes normally."""
        parser = PdfFileParser()

        with patch("app.services.file_parser.MAX_PDF_PAGES", 5):
            upload = UploadFile(
                filename="sample.pdf",
                file=io.BytesIO(build_pdf_bytes(["Page 1", "Page 2"])),
                headers=Headers({"content-type": "application/pdf"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("Page 1", parsed.content)
            self.assertIn("Page 2", parsed.content)

    async def test_ocr_page_limit_exceeded_raises_error(self) -> None:
        """OCR page count > MAX_OCR_PAGES raises before _extract_pdf_via_ocr is called."""
        parser = PdfFileParser()
        ocr_called = False

        def _assert_ocr_not_called(raw: bytes) -> str:
            nonlocal ocr_called
            ocr_called = True
            return "should not reach here"

        with patch("app.services.file_parser.MAX_OCR_PAGES", 1), patch.object(
            parser, "_extract_pdf_via_ocr", _assert_ocr_not_called
        ):
            upload = UploadFile(
                filename="scan.pdf",
                file=io.BytesIO(build_blank_pdf_bytes(page_count=2)),
                headers=Headers({"content-type": "application/pdf"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("OCR page count", str(ctx.exception))
            self.assertIn("2", str(ctx.exception))
            self.assertIn("1", str(ctx.exception))

        self.assertFalse(ocr_called, "_extract_pdf_via_ocr must NOT be called when page count exceeds limit")

    async def test_ocr_timeout_raises_error(self) -> None:
        """OCR subprocess timeout raises ProcessingLimitExceededError within page limit."""
        parser = OcrTimeoutPdfFileParser()

        with patch("app.services.file_parser.MAX_OCR_PAGES", 5), patch(
            "app.services.file_parser.OCR_TOOL_TIMEOUT_SECONDS", 1
        ):
            upload = UploadFile(
                filename="scan.pdf",
                file=io.BytesIO(build_blank_pdf_bytes(page_count=2)),
                headers=Headers({"content-type": "application/pdf"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("timeout", str(ctx.exception).lower())

    def test_run_command_timeout_conversion(self) -> None:
        """_run_command converts subprocess.TimeoutExpired to ProcessingLimitExceededError."""
        parser = PdfFileParser()

        with patch(
            "app.services.file_parser.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["test"], timeout=1),
        ), self.assertRaises(ProcessingLimitExceededError) as ctx:
            parser._run_command(["test"], timeout=1)

        self.assertIn("timeout", str(ctx.exception).lower())

    async def test_ocr_within_page_limit_succeeds(self) -> None:
        """OCR page count within limit processes successfully."""
        parser = OcrSimulatedPdfFileParser(simulated_page_count=2, ocr_text="Simulated OCR text")

        with patch("app.services.file_parser.MAX_OCR_PAGES", 5):
            upload = UploadFile(
                filename="scan.pdf",
                file=io.BytesIO(build_blank_pdf_bytes(page_count=2)),
                headers=Headers({"content-type": "application/pdf"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("Simulated OCR text", parsed.content)


class OfficeXmlProcessingGuardrailTest(unittest.IsolatedAsyncioTestCase):
    """Tests for DOCX/HWPX internal XML size guardrails using monkeypatch only."""

    # ─── DOCX ───────────────────────────────────────────────

    async def test_docx_entry_size_exceeded_raises_error(self) -> None:
        """DOCX word/document.xml entry size > MAX_OFFICE_XML_ENTRY_BYTES raises."""
        parser = DocxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_ENTRY_BYTES", 1):
            upload = UploadFile(
                filename="sample.docx",
                file=io.BytesIO(build_docx_bytes(["Some real content"])),
                headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("DOCX XML entry", str(ctx.exception))
            self.assertIn("word/document.xml", str(ctx.exception))

    async def test_docx_entry_size_within_limit_succeeds(self) -> None:
        """DOCX entry size within limit parses successfully."""
        parser = DocxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_ENTRY_BYTES", 5 * 1024 * 1024):
            upload = UploadFile(
                filename="sample.docx",
                file=io.BytesIO(build_docx_bytes(["Hello", "contact@ipu.co.kr"])),
                headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("Hello", parsed.content)
            self.assertIn("contact@ipu.co.kr", parsed.content)

    # ─── HWPX: Entry Size ──────────────────────────────────

    async def test_hwpx_entry_size_exceeded_raises_error(self) -> None:
        """HWPX section XML entry size > MAX_OFFICE_XML_ENTRY_BYTES raises."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_ENTRY_BYTES", 1):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([["First paragraph", "contact@ipu.co.kr"]])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("HWPX XML entry", str(ctx.exception))

    async def test_hwpx_entry_size_within_limit_succeeds(self) -> None:
        """HWPX entry size within limit parses successfully."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_ENTRY_BYTES", 5 * 1024 * 1024):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([["첫 문단", "contact@ipu.co.kr"]])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("첫 문단", parsed.content)
            self.assertIn("contact@ipu.co.kr", parsed.content)

    # ─── HWPX: Total Size ──────────────────────────────────

    async def test_hwpx_total_size_exceeded_raises_error(self) -> None:
        """HWPX section XML total size > MAX_OFFICE_XML_TOTAL_BYTES raises."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_TOTAL_BYTES", 1):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([["Some text"]])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("total size", str(ctx.exception))
            self.assertIn("1", str(ctx.exception))

    async def test_hwpx_total_size_within_limit_succeeds(self) -> None:
        """HWPX total size within limit parses successfully."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_OFFICE_XML_TOTAL_BYTES", 20 * 1024 * 1024):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([["둘째 문단"]])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("둘째 문단", parsed.content)

    # ─── HWPX: Section Count ───────────────────────────────

    async def test_hwpx_section_count_exceeded_raises_error(self) -> None:
        """HWPX section XML file count > MAX_HWPX_SECTION_XML_FILES raises."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_HWPX_SECTION_XML_FILES", 1):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([
                    ["Section 1"],
                    ["Section 2"],
                ])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            with self.assertRaises(ProcessingLimitExceededError) as ctx:
                await parser.parse(upload)

            self.assertIn("file count", str(ctx.exception))
            self.assertIn("2", str(ctx.exception))
            self.assertIn("1", str(ctx.exception))

    async def test_hwpx_section_count_within_limit_succeeds(self) -> None:
        """HWPX section count within limit parses successfully."""
        parser = HwpxFileParser()

        with patch("app.services.file_parser.MAX_HWPX_SECTION_XML_FILES", 10):
            upload = UploadFile(
                filename="sample.hwpx",
                file=io.BytesIO(build_hwpx_bytes([
                    ["Section A"],
                    ["Section B"],
                ])),
                headers=Headers({"content-type": "application/haansofthwpx"}),
            )
            upload.size = len(upload.file.getvalue())

            parsed = await parser.parse(upload)

            self.assertIn("Section A", parsed.content)
            self.assertIn("Section B", parsed.content)
