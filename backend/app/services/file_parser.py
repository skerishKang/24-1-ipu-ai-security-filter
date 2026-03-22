from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Protocol
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from fastapi import UploadFile
from pypdf import PdfReader

from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidEncodingError,
    UnsupportedFileTypeError,
)

MAX_UPLOAD_FILE_BYTES = 104_857_600
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
    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.txt"
        content_type = file.content_type or "text/plain"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_TEXT_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_TEXT_CONTENT_TYPES:
            raise UnsupportedFileTypeError("text/plain, text/markdown, text/csv")

        if file_size is not None and file_size > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

        raw = await file.read()
        if len(raw) > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

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
    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.pdf"
        content_type = file.content_type or "application/pdf"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_PDF_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_PDF_CONTENT_TYPES:
            raise UnsupportedFileTypeError("application/pdf")

        if file_size is not None and file_size > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

        raw = await file.read()
        if len(raw) > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

        try:
            reader = PdfReader(io.BytesIO(raw))
        except Exception as error:
            raise ValueError("PDF 파일을 해석할 수 없습니다.") from error

        if reader.is_encrypted:
            raise ValueError("암호화된 PDF 파일은 아직 지원하지 않습니다.")

        extracted_pages = []
        for page in reader.pages:
            text = self._extract_page_text(page)
            if text:
                extracted_pages.append(text)

        content = "\n".join(extracted_pages).strip()
        if not content:
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
        except Exception:
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
                    ]
                )

                image_paths = sorted(tmpdir_path.glob("page-*.png"))
                extracted_pages = []
                for image_path in image_paths:
                    ocr_text = self._run_tesseract(image_path)
                    normalized = self._normalize_extracted_text(ocr_text)
                    if normalized:
                        extracted_pages.append(normalized)
                return "\n".join(extracted_pages).strip()
        except subprocess.CalledProcessError:
            return ""

    def _is_ocr_toolchain_available(self) -> bool:
        return shutil.which("pdftoppm") is not None and shutil.which("tesseract") is not None

    def _run_tesseract(self, image_path: Path) -> str:
        try:
            return self._run_command(
                ["tesseract", str(image_path), "stdout", "-l", "kor+eng"],
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            return self._run_command(
                ["tesseract", str(image_path), "stdout"],
                capture_output=True,
            )

    def _run_command(self, command: list[str], *, capture_output: bool = False) -> str:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=capture_output,
            text=True,
        )
        return completed.stdout if capture_output else ""


class DefaultFileParser:
    def __init__(self) -> None:
        self._text_parser = TextFileParser()
        self._pdf_parser = PdfFileParser()
        self._docx_parser = DocxFileParser()
        self._hwpx_parser = HwpxFileParser()

    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = (file.filename or "").lower()
        if any(filename.endswith(extension) for extension in UNSUPPORTED_HWP_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".hwpx, .pdf, .docx, .txt (바이너리 .hwp 미지원)")
        if filename.endswith(".pdf"):
            return await self._pdf_parser.parse(file)
        if filename.endswith(".docx"):
            return await self._docx_parser.parse(file)
        if filename.endswith(".hwpx"):
            return await self._hwpx_parser.parse(file)
        return await self._text_parser.parse(file)


class DocxFileParser:
    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.docx"
        content_type = file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_DOCX_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_DOCX_CONTENT_TYPES:
            raise UnsupportedFileTypeError(".docx")

        if file_size is not None and file_size > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

        raw = await file.read()
        if len(raw) > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

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
    async def parse(self, file: UploadFile) -> ParsedFileContent:
        filename = file.filename or "uploaded.hwpx"
        content_type = file.content_type or "application/zip"
        file_size = getattr(file, "size", None)
        lowered_filename = filename.lower()

        if not any(lowered_filename.endswith(extension) for extension in SUPPORTED_HWPX_FILE_EXTENSIONS):
            raise UnsupportedFileTypeError(".txt, .md, .csv, .pdf, .docx, .hwpx")

        if content_type not in SUPPORTED_HWPX_CONTENT_TYPES:
            raise UnsupportedFileTypeError(".hwpx")

        if file_size is not None and file_size > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

        raw = await file.read()
        if len(raw) > MAX_UPLOAD_FILE_BYTES:
            raise FileTooLargeError()

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
                sections = [archive.read(name) for name in section_names]
        except BadZipFile as error:
            raise ValueError("HWPX 파일을 해석할 수 없습니다.") from error

        paragraphs = []
        namespace = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
        for section_xml in sections:
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
        return "\n".join(paragraphs).strip()
