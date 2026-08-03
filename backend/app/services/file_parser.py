from __future__ import annotations

import io
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile
from pypdf import PdfReader

from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidEncodingError,
    ProcessingLimitExceededError,
    UnsupportedFileTypeError,
)
from app.services.upload_reader import read_limited_upload

MAX_UPLOAD_FILE_BYTES = 104_857_600
MAX_EXTRACTED_TEXT_CHARS = 100_000
MAX_PDF_PAGES = 50
MAX_OCR_PAGES = 5
OCR_TOOL_TIMEOUT_SECONDS = 15
MAX_OFFICE_XML_ENTRY_BYTES = 5 * 1024 * 1024
MAX_OFFICE_XML_TOTAL_BYTES = 20 * 1024 * 1024
MAX_HWPX_SECTION_XML_FILES = 200
SUPPORTED_TEXT_FILE_EXTENSIONS = {".txt", ".md", ".csv"}
SUPPORTED_TEXT_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/csv",
    "application/octet-stream",
}
SUPPORTED_PDF_FILE_EXTENSIONS = {".pdf"}
SUPPORTED_PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}
SUPPORTED_DOCX_FILE_EXTENSIONS = {".docx"}
SUPPORTED_DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "application/octet-stream",
}
SUPPORTED_HWPX_FILE_EXTENSIONS = {".hwpx"}
SUPPORTED_HWPX_CONTENT_TYPES = {
    "application/zip",
    "application/octet-stream",
    "application/haansofthwpx",
}
UNSUPPORTED_HWP_FILE_EXTENSIONS = {".hwp"}


@dataclass(frozen=True)
class ParsedFileContent:
    content: str
    normalized_content_type: str
    filename: str


class FileParser(Protocol):
    async def parse(self, file: UploadFile) -> ParsedFileContent: ...


class TextFileParser:
    def __init__(self, max_upload_bytes: int = MAX_UPLOAD_FILE_BYTES) -> None:
        self.max_upload_bytes = max_upload_bytes

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.txt"
        content_type = file.content_type or "text/plain"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_TEXT_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_TEXT_CONTENT_TYPES:
            raise UnsupportedFileTypeError("text/plain, text/markdown, text/csv")

        if file_size is not None and file_size > self.max_upload_bytes:
            raise FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024))

        raw = await read_limited_upload(
            file,
            self.max_upload_bytes,
            error_factory=lambda: FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024)),
        )

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise InvalidEncodingError() from error

        if not text.strip():
            raise EmptyFileError()

        return ParsedFileContent(
            content=text,
            normalized_content_type=self._normalize_content_type(Path(filename).suffix.lower()),
            filename=filename,
        )

    def _normalize_content_type(self, suffix: str) -> str:
        if suffix == ".md":
            return "text/markdown"
        if suffix == ".csv":
            return "text/csv"
        return "text/plain"


class PdfFileParser:
    def __init__(self, max_upload_bytes: int = MAX_UPLOAD_FILE_BYTES) -> None:
        self.max_upload_bytes = max_upload_bytes

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.pdf"
        content_type = file.content_type or "application/pdf"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_PDF_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_PDF_CONTENT_TYPES:
            raise UnsupportedFileTypeError("application/pdf")

        if file_size is not None and file_size > self.max_upload_bytes:
            raise FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024))

        raw = await read_limited_upload(
            file,
            self.max_upload_bytes,
            error_factory=lambda: FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024)),
        )

        try:
            reader = PdfReader(io.BytesIO(raw))
        except Exception as error:
            raise ValueError("PDF 파일을 해석할 수 없습니다.") from error

        if reader.is_encrypted:
            raise ValueError("암호화된 PDF 파일은 아직 지원하지 않습니다.")

        if len(reader.pages) > MAX_PDF_PAGES:
            raise ProcessingLimitExceededError(
                f"PDF page count {len(reader.pages)} exceeds the processing limit of {MAX_PDF_PAGES} pages."
            )

        extracted_pages = []
        for page in reader.pages:
            text = self._extract_page_text(page)
            if text:
                extracted_pages.append(text)

        content = "\n".join(extracted_pages).strip()
        if not content:
            if len(reader.pages) > MAX_OCR_PAGES:
                raise ProcessingLimitExceededError(
                    f"OCR page count {len(reader.pages)} exceeds the processing limit of {MAX_OCR_PAGES} pages."
                )
            content = self._extract_pdf_via_ocr(raw)
        if not content:
            raise ValueError("텍스트를 추출할 수 있는 PDF 파일만 지원합니다.")

        return ParsedFileContent(
            content=content,
            normalized_content_type="application/pdf",
            filename=filename,
        )

    def _extract_page_text(self, page: object) -> str:
        extracted = self._call_extract_text(page)
        if not extracted.strip():
            extracted = self._call_extract_text(page, extraction_mode="layout")
        return self._normalize_extracted_text(extracted)

    def _call_extract_text(self, page: object, **kwargs: object) -> str:
        try:
            extracted = page.extract_text(**kwargs)
        except TypeError:
            extracted = page.extract_text()
        except Exception:  # noqa: BLE001
            # Fallback boundary: a malformed or vendor-specific PDF page must not
            # fail the whole extraction; treat it as empty text.
            return ""
        return extracted or ""

    def _normalize_extracted_text(self, text: str) -> str:
        cleaned = text.replace("\x00", "")
        normalized_lines = []
        for raw_line in cleaned.splitlines():
            normalized = re.sub(r"[ \t\u00a0]+", " ", raw_line).strip()
            if normalized:
                normalized_lines.append(normalized)
        return "\n".join(normalized_lines)

    def _extract_pdf_via_ocr(self, raw: bytes) -> str:
        if not self._is_ocr_toolchain_available():
            raise ValueError("스캔형 PDF OCR을 위한 로컬 도구가 없습니다. tesseract 와 pdftoppm 설치 후 다시 시도해 주세요.")
        try:
            with tempfile.TemporaryDirectory(prefix="ipu-pdf-ocr-") as tmpdir:
                tmpdir_path = Path(tmpdir)
                pdf_path = tmpdir_path / "input.pdf"
                pdf_path.write_bytes(raw)
                image_prefix = tmpdir_path / "page"
                self._run_command(
                    [
                        "pdftoppm",
                        "-png",
                        str(pdf_path),
                        str(image_prefix),
                    ],
                    timeout=OCR_TOOL_TIMEOUT_SECONDS,
                )

                image_paths = sorted(tmpdir_path.glob("page-*.png"))
                if len(image_paths) > MAX_OCR_PAGES:
                    raise ProcessingLimitExceededError(
                        f"OCR page count {len(image_paths)} exceeds the processing limit of {MAX_OCR_PAGES} pages."
                    )
                extracted_pages = []
                for image_path in image_paths:
                    ocr_text = self._run_tesseract(image_path, timeout=OCR_TOOL_TIMEOUT_SECONDS)
                    normalized = self._normalize_extracted_text(ocr_text)
                    if normalized:
                        extracted_pages.append(normalized)
                return "\n".join(extracted_pages).strip()
        except subprocess.CalledProcessError:
            return ""

    def _is_ocr_toolchain_available(self) -> bool:
        return shutil.which("pdftoppm") is not None and shutil.which("tesseract") is not None

    def _run_tesseract(self, image_path: Path, timeout: int = 15) -> str:
        try:
            return self._run_command(
                ["tesseract", str(image_path), "stdout", "-l", "kor+eng"],
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError:
            return self._run_command(
                ["tesseract", str(image_path), "stdout"],
                capture_output=True,
                timeout=timeout,
            )

    def _run_command(self, command: list[str], *, capture_output: bool = False, timeout: int | None = None) -> str:
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise ProcessingLimitExceededError(
                f"OCR command exceeded the processing timeout of {timeout} seconds."
            ) from error
        return completed.stdout if capture_output else ""


class DefaultFileParser:
    def __init__(
        self,
        max_upload_bytes: int = MAX_UPLOAD_FILE_BYTES,
        max_extracted_text_chars: int = MAX_EXTRACTED_TEXT_CHARS,
    ) -> None:
        self.max_extracted_text_chars = max_extracted_text_chars
        self._text_parser = TextFileParser(max_upload_bytes=max_upload_bytes)
        self._pdf_parser = PdfFileParser(max_upload_bytes=max_upload_bytes)
        self._docx_parser = DocxFileParser(max_upload_bytes=max_upload_bytes)
        self._hwpx_parser = HwpxFileParser(max_upload_bytes=max_upload_bytes)

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = (file.filename or "").lower()
        if any(filename.endswith(extension) for extension in UNSUPPORTED_HWP_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".hwpx, .pdf, .docx, .txt (바이너리 .hwp 미지원)")
        if filename.endswith(".pdf"):
            return self._enforce_extracted_text_limit(await self._pdf_parser.parse(file))
        if filename.endswith(".docx"):
            return self._enforce_extracted_text_limit(await self._docx_parser.parse(file))
        if filename.endswith(".hwpx"):
            return self._enforce_extracted_text_limit(await self._hwpx_parser.parse(file))
        return self._enforce_extracted_text_limit(await self._text_parser.parse(file))

    def _enforce_extracted_text_limit(self, parsed: ParsedFileContent) -> ParsedFileContent:
        if len(parsed.content) <= self.max_extracted_text_chars:
            return parsed
        raise ProcessingLimitExceededError(
            f"Extracted text length {len(parsed.content)} exceeds the processing limit of {self.max_extracted_text_chars} characters."
        )


class DocxFileParser:
    def __init__(self, max_upload_bytes: int = MAX_UPLOAD_FILE_BYTES) -> None:
        self.max_upload_bytes = max_upload_bytes

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.docx"
        content_type = file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_DOCX_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_DOCX_CONTENT_TYPES:
            raise UnsupportedFileTypeError(".docx")

        if file_size is not None and file_size > self.max_upload_bytes:
            raise FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024))

        raw = await read_limited_upload(
            file,
            self.max_upload_bytes,
            error_factory=lambda: FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024)),
        )

        content = self._extract_docx_text(raw)
        if not content:
            raise ValueError("본문 텍스트를 추출할 수 있는 DOCX 파일만 지원합니다.")

        return ParsedFileContent(
            content=content,
            normalized_content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )

    def _extract_docx_text(self, raw: bytes) -> str:
        try:
            with ZipFile(io.BytesIO(raw)) as archive:
                docx_entry = archive.getinfo("word/document.xml")
                if docx_entry.file_size > MAX_OFFICE_XML_ENTRY_BYTES:
                    raise ProcessingLimitExceededError(
                        f"DOCX XML entry word/document.xml exceeds the processing limit of {MAX_OFFICE_XML_ENTRY_BYTES} bytes."
                    )
                xml = archive.read("word/document.xml")
        except KeyError as error:
            raise ValueError("DOCX 본문 문서를 찾을 수 없습니다.") from error
        except BadZipFile as error:
            raise ValueError("DOCX 파일을 해석할 수 없습니다.") from error

        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise ValueError("DOCX XML을 해석할 수 없습니다.") from error

        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:body/w:p", namespace):
            runs = [
                text_node.text or ""
                for text_node in paragraph.findall(".//w:t", namespace)
                if (text_node.text or "").strip()
            ]
            if runs:
                paragraphs.append("".join(runs).strip())
        return "\n".join(paragraphs).strip()


class HwpxFileParser:
    def __init__(self, max_upload_bytes: int = MAX_UPLOAD_FILE_BYTES) -> None:
        self.max_upload_bytes = max_upload_bytes

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.hwpx"
        content_type = file.content_type or "application/zip"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_HWPX_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_HWPX_CONTENT_TYPES:
            raise UnsupportedFileTypeError(".hwpx")

        if file_size is not None and file_size > self.max_upload_bytes:
            raise FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024))

        raw = await read_limited_upload(
            file,
            self.max_upload_bytes,
            error_factory=lambda: FileTooLargeError(max_size_mb=self.max_upload_bytes // (1024 * 1024)),
        )

        content = self._extract_hwpx_text(raw)
        if not content:
            raise ValueError("본문 텍스트를 추출할 수 있는 HWPX 파일만 지원합니다.")

        return ParsedFileContent(
            content=content,
            normalized_content_type="application/haansofthwpx",
            filename=filename,
        )

    def _extract_hwpx_text(self, raw: bytes) -> str:
        try:
            with ZipFile(io.BytesIO(raw)) as archive:
                section_names = sorted(
                    name
                    for name in archive.namelist()
                    if name.startswith("Contents/section") and name.endswith(".xml")
                )
                if not section_names:
                    raise ValueError("HWPX 본문 section XML을 찾을 수 없습니다.")

                if len(section_names) > MAX_HWPX_SECTION_XML_FILES:
                    raise ProcessingLimitExceededError(
                        f"HWPX section XML file count {len(section_names)} "
                        f"exceeds the processing limit of {MAX_HWPX_SECTION_XML_FILES}."
                    )

                total_xml_size = 0
                for name in section_names:
                    info = archive.getinfo(name)
                    if info.file_size > MAX_OFFICE_XML_ENTRY_BYTES:
                        raise ProcessingLimitExceededError(
                            f"HWPX XML entry {name} size {info.file_size} "
                            f"exceeds the processing limit of {MAX_OFFICE_XML_ENTRY_BYTES} bytes."
                        )
                    total_xml_size += info.file_size

                if total_xml_size > MAX_OFFICE_XML_TOTAL_BYTES:
                    raise ProcessingLimitExceededError(
                        f"HWPX section XML total size {total_xml_size} "
                        f"exceeds the processing limit of {MAX_OFFICE_XML_TOTAL_BYTES} bytes."
                    )

                paragraphs = []
                namespace = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
                for name in section_names:
                    section_xml = archive.read(name)
                    try:
                        root = ElementTree.fromstring(section_xml)
                    except ElementTree.ParseError as error:
                        raise ValueError("HWPX XML을 해석할 수 없습니다.") from error

                    for paragraph in root.findall(".//hp:p", namespace):
                        texts = [
                            (text_node.text or "").strip()
                            for text_node in paragraph.findall(".//hp:t", namespace)
                            if (text_node.text or "").strip()
                        ]
                        if texts:
                            paragraphs.append(" ".join(texts))
        except BadZipFile as error:
            raise ValueError("HWPX 파일을 해석할 수 없습니다.") from error

        return "\n".join(paragraphs).strip()
