from __future__ import annotations

from dataclasses import dataclass
import io
import unittest

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.file_parser import PdfFileParser
from engine.src.manual_preview_engine import ManualPreviewEngine


@dataclass(frozen=True)
class PdfQualitySample:
    sample_id: str
    description: str
    parser_mode: str
    page_texts: tuple[str, ...]
    expected_types: tuple[str, ...]
    minimum_detections: int


PDF_QUALITY_SAMPLES: tuple[PdfQualitySample, ...] = (
    PdfQualitySample(
        sample_id="text_layer_contact_sheet",
        description="텍스트 레이어 PDF 연락처 시트",
        parser_mode="text-layer",
        page_texts=(
            "Contact sheet\nsecurity@ipu.co.kr\n010-2222-3333\ncontract amount 120,000,000원",
        ),
        expected_types=("EMAIL", "PHONE"),
        minimum_detections=2,
    ),
    PdfQualitySample(
        sample_id="text_layer_multi_page_report",
        description="멀티페이지 보고서형 PDF",
        parser_mode="text-layer",
        page_texts=(
            "Weekly report",
            "support@ipu.co.kr\n02 3456 7890\nbudget 75,000,000원 review",
        ),
        expected_types=("EMAIL", "PHONE"),
        minimum_detections=2,
    ),
    PdfQualitySample(
        sample_id="ocr_like_contact_sheet",
        description="OCR fallback 연락처 시트",
        parser_mode="ocr-fallback",
        page_texts=(
            "미래전자\n김민수 부장\nsecurity@ipu.co.kr\n010 2222 3333\n계약금액 120,000,000 원",
        ),
        expected_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        minimum_detections=5,
    ),
    PdfQualitySample(
        sample_id="ocr_like_internal_report",
        description="OCR fallback 내부 보고서",
        parser_mode="ocr-fallback",
        page_texts=(
            "아이피유테크 주간 보고\n이준호 과장\nsupport@ipu.co.kr\n02 3456 7890\n예산 75,000,000 원 검토",
        ),
        expected_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        minimum_detections=5,
    ),
)


class PdfQualitySamplesTest(unittest.IsolatedAsyncioTestCase):
    async def test_pdf_quality_samples_drive_expected_detections(self) -> None:
        engine = ManualPreviewEngine()

        for sample in PDF_QUALITY_SAMPLES:
            with self.subTest(sample=sample.sample_id):
                parser = self._build_parser(sample)
                upload = UploadFile(
                    filename=f"{sample.sample_id}.pdf",
                    file=io.BytesIO(self._build_pdf_bytes(sample)),
                    headers=Headers({"content-type": "application/pdf"}),
                )
                upload.size = len(upload.file.getvalue())

                parsed = await parser.parse(upload)
                preview = engine.manual_preview(
                    content=parsed.content,
                    session_id=f"pdf-quality-{sample.sample_id}",
                    policy="strict_token",
                )

                detected_types = {item["type"] for item in preview["detections"]}
                self.assertGreaterEqual(len(preview["detections"]), sample.minimum_detections)
                for expected_type in sample.expected_types:
                    self.assertIn(expected_type, detected_types)
                    self.assertIn(f"[{expected_type}_", preview["replaced_text"])

    def _build_parser(self, sample: PdfQualitySample) -> PdfFileParser:
        if sample.parser_mode == "ocr-fallback":
            return OcrFallbackPdfFileParser("\n".join(sample.page_texts))
        return PdfFileParser()

    def _build_pdf_bytes(self, sample: PdfQualitySample) -> bytes:
        if sample.parser_mode == "ocr-fallback":
            return build_blank_pdf_bytes()
        return build_pdf_bytes(list(sample.page_texts))


class OcrFallbackPdfFileParser(PdfFileParser):
    def __init__(self, ocr_text: str) -> None:
        self._ocr_text = ocr_text

    def _extract_pdf_via_ocr(self, raw: bytes) -> str:
        return self._ocr_text


def build_blank_pdf_bytes() -> bytes:
    from pypdf import PdfWriter

    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=200)
    writer.write(buffer)
    return buffer.getvalue()


def build_pdf_bytes(page_texts: list[str]) -> bytes:
    objects = []
    page_references = []

    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    for index, text in enumerate(page_texts):
        page_object_number = 3 + (index * 2)
        content_object_number = page_object_number + 1
        page_references.append(f"{page_object_number} 0 R".encode("ascii"))

        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 120 Td ({escaped}) Tj ET".encode("utf-8")

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
