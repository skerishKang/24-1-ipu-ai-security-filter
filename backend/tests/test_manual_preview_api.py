import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import wave

import httpx
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.api.routes.manual_mode import get_manual_preview_service
from app.core.exceptions import ProcessingLimitExceededError
from app.main import create_app
from app.services.manual_preview_service import ManualPreviewService




class FakeAudioTranscriber:
    async def transcribe(self, file: UploadFile):
        return type(
            "TranscribedAudio",
            (),
            {
                "text": "아이피유테크 홍길동 이사가 contact@ipu.co.kr 로 연락합니다.",
                "content_type": file.content_type or "audio/wav",
                "filename": file.filename or "sample.wav",
                "engine_name": "fake-whisper",
            },
        )()


class ManualPreviewApiSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "manual_preview_sessions.sqlite3"
        os.environ["IPU_SESSION_STORE_PATH"] = str(db_path)
        os.environ["IPU_SESSION_STORE_KIND"] = "sqlite"
        os.environ["IPU_AUDIO_TRANSCRIBER"] = "placeholder"
        self.app = create_app()
        service = ManualPreviewService()
        self.app.state.manual_preview_service = service
        self.app.dependency_overrides[get_manual_preview_service] = lambda request=None: service
        self.manual_preview_service = service

        transport = httpx.ASGITransport(app=self.app)
        self.client = httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        self.app.dependency_overrides.clear()
        os.environ.pop("IPU_SESSION_STORE_PATH", None)
        os.environ.pop("IPU_SESSION_STORE_KIND", None)
        os.environ.pop("IPU_AUDIO_TRANSCRIBER", None)
        self.temp_dir.cleanup()

    async def test_health_endpoint(self) -> None:
        response = await self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "healthy")
        self.assertIn("mode", body)

    async def test_manual_preview_endpoint_shape(self) -> None:
        payload = {
            "content": (
                "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 "
                "010-1234-5678 정보를 포함한 제안서를 검토해 주세요."
            ),
            "content_type": "text",
            "policy": "default",
        }

        response = await self.client.post("/api/v1/mode/manual-preview", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()

        for field in (
            "session_id",
            "restore_token",
            "original_text",
            "replaced_text",
            "detections",
            "replacements",
            "report",
            "copy_ready_prompt",
        ):
            self.assertIn(field, body)

        self.assertEqual(body["original_text"], payload["content"])
        self.assertNotEqual(body["replaced_text"], body["original_text"])
        self.assertTrue(body["restore_token"])
        self.assertIsInstance(body["detections"], list)
        self.assertIsInstance(body["replacements"], list)
        self.assertGreaterEqual(len(body["detections"]), 1)
        self.assertGreaterEqual(len(body["replacements"]), 1)

        report = body["report"]
        for field in (
            "total_detections",
            "risk_level",
            "strategy",
            "review_status",
        ):
            self.assertIn(field, report)
        self.assertIn(report["risk_level"], {"low-risk", "moderate-risk", "high-risk"})
        self.assertIn(report["strategy"], {"alias", "strict_token"})
        self.assertIn(report["review_status"], {"clean", "review-required"})

        first_detection = body["detections"][0]
        for field in ("type", "label", "start", "end", "score", "note"):
            self.assertIn(field, first_detection)

        first_replacement = body["replacements"][0]
        for field in ("type", "original", "replaced", "reason"):
            self.assertIn(field, first_replacement)

    async def test_manual_preview_endpoint_rejects_unknown_policy(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview",
            json={
                "content": "contact@ipu.co.kr",
                "content_type": "text",
                "policy": "balanced",
            },
        )

        self.assertEqual(response.status_code, 422)

    async def test_manual_preview_file_endpoint_shape(self) -> None:
        files = {
            "file": ("sample.txt", "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.", "text/plain"),
        }
        data = {"policy": "default"}

        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files=files,
            data=data,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("session_id", body)
        self.assertIn("restore_token", body)
        self.assertIn("replaced_text", body)
        self.assertIn("report", body)
        self.assertTrue(body["restore_token"])
        self.assertNotEqual(body["replaced_text"], body["original_text"])
        self.assertIsInstance(body["detections"], list)
        self.assertIsInstance(body["replacements"], list)

    async def test_manual_preview_file_accepts_markdown_file(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.md",
                    "# 고객 메모\ncontact@ipu.co.kr\n010-2222-3333",
                    "text/markdown",
                )
            },
            data={"policy": "strict_token"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("[EMAIL_", body["replaced_text"])
        self.assertIn("[PHONE_", body["replaced_text"])

    async def test_manual_preview_file_accepts_csv_file(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.csv",
                    "name,email\n홍길동,contact@ipu.co.kr",
                    "text/csv",
                )
            },
            data={"policy": "default"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("[EMAIL_ALIAS_", body["replaced_text"])

    async def test_manual_preview_file_accepts_pdf_file(self) -> None:
        pdf_bytes = build_pdf_bytes(["Contact contact@ipu.co.kr"])
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
            data={"policy": "strict_token"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("[EMAIL_", body["replaced_text"])

    async def test_manual_preview_file_accepts_docx_file(self) -> None:
        docx_bytes = build_docx_bytes(["아이피유테크 홍길동 이사", "contact@ipu.co.kr"])
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.docx",
                    docx_bytes,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            data={"policy": "strict_token"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("[EMAIL_", body["replaced_text"])

    async def test_manual_preview_file_accepts_hwpx_file(self) -> None:
        hwpx_bytes = build_hwpx_bytes([["아이피유테크 홍길동 이사", "contact@ipu.co.kr"]])
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.hwpx",
                    hwpx_bytes,
                    "application/haansofthwpx",
                )
            },
            data={"policy": "strict_token"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("[EMAIL_", body["replaced_text"])

    async def test_manual_preview_audio_endpoint_returns_not_implemented_placeholder(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/audio",
            files={
                "file": (
                    "sample.wav",
                    build_wav_bytes(duration_seconds=0.1),
                    "audio/wav",
                )
            },
            data={"policy": "default"},
        )

        self.assertEqual(response.status_code, 501)
        self.assertIn("STT", response.json()["detail"])

    async def test_manual_preview_audio_endpoint_uses_transcriber_output(self) -> None:
        service = self.manual_preview_service
        original_transcriber = service.audio_transcriber
        service.audio_transcriber = FakeAudioTranscriber()
        try:
            response = await self.client.post(
                "/api/v1/mode/manual-preview/audio",
                files={
                    "file": (
                        "sample.wav",
                        build_wav_bytes(duration_seconds=0.1),
                        "audio/wav",
                    )
                },
                data={"policy": "default"},
            )
        finally:
            service.audio_transcriber = original_transcriber

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["original_text"], "아이피유테크 홍길동 이사가 contact@ipu.co.kr 로 연락합니다.")
        self.assertIn("[EMAIL_ALIAS_", body["replaced_text"])

    async def test_manual_preview_audio_rejects_over_duration_wav(self) -> None:
        with patch("app.services.audio_transcriber.MAX_AUDIO_DURATION_SECONDS", 0.001):
            response = await self.client.post(
                "/api/v1/mode/manual-preview/audio",
                files={
                    "file": (
                        "sample.wav",
                        build_wav_bytes(duration_seconds=0.1),
                        "audio/wav",
                    )
                },
                data={"policy": "default"},
            )

        self.assertEqual(response.status_code, 413)
        self.assertIn("duration", response.json()["detail"].lower())
        self.assertIn("0.001", response.json()["detail"])

    async def test_manual_preview_file_rejects_unsupported_extension(self) -> None:
        files = {
            "file": ("sample.pdf", "fake pdf content", "application/pdf"),
        }

        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files=files,
            data={"policy": "default"},
        )

        self.assertEqual(response.status_code, 415)

    async def test_manual_preview_file_rejects_binary_hwp_with_conversion_guidance(self) -> None:
        response = await self.client.post(
            "/api/v1/mode/manual-preview/file",
            files={
                "file": (
                    "sample.hwp",
                    b"fake-hwp",
                    "application/x-hwp",
                )
            },
            data={"policy": "default"},
        )

        self.assertEqual(response.status_code, 415)
        self.assertIn(".hwpx", response.json()["detail"])

    async def test_manual_preview_file_returns_ocr_tool_guidance_for_scan_pdf_without_toolchain(self) -> None:
        original_service = self.manual_preview_service
        original_parser = original_service.file_parser._pdf_parser
        original_service.file_parser._pdf_parser = MissingOcrToolPdfFileParser()
        try:
            response = await self.client.post(
                "/api/v1/mode/manual-preview/file",
                files={
                    "file": (
                        "scan.pdf",
                        build_blank_pdf_bytes(),
                        "application/pdf",
                    )
                },
                data={"policy": "default"},
            )
        finally:
            original_service.file_parser._pdf_parser = original_parser

        self.assertEqual(response.status_code, 415)
        self.assertIn("tesseract", response.json()["detail"])

    async def test_manual_preview_file_rejects_oversized_text_file(self) -> None:
        oversized = UploadFile(
            filename="sample.txt",
            file=io.BytesIO(b"short"),
            headers=Headers({"content-type": "text/plain"}),
        )
        oversized.size = 104_857_601

        service = self.manual_preview_service

        with self.assertRaisesRegex(ValueError, "100MB"):
            await service.build_file_preview(file=oversized, policy="default")

    async def test_manual_preview_file_returns_413_for_processing_limit_exceeded(self) -> None:
        original_service = self.manual_preview_service
        original_parser = original_service.file_parser

        class LimitExceededParser:
            async def parse(self, file):
                raise ProcessingLimitExceededError("PDF page count 51 exceeds the processing limit of 50 pages.")

        original_service.file_parser = LimitExceededParser()
        try:
            response = await self.client.post(
                "/api/v1/mode/manual-preview/file",
                files={
                    "file": ("sample.pdf", b"fake-pdf", "application/pdf"),
                },
                data={"policy": "default"},
            )
        finally:
            original_service.file_parser = original_parser

        self.assertEqual(response.status_code, 413)
        self.assertIn("PDF page count", response.json()["detail"])
        self.assertIn("50", response.json()["detail"])

    async def test_manual_preview_policy_is_reflected_in_report(self) -> None:
        strict_payload = {
            "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
            "content_type": "text",
            "policy": "strict_token",
        }

        strict_response = await self.client.post("/api/v1/mode/manual-preview", json=strict_payload)
        self.assertEqual(strict_response.status_code, 200)
        self.assertEqual(strict_response.json()["report"]["strategy"], "strict_token")

        default_response = await self.client.post(
            "/api/v1/mode/manual-preview",
            json={**strict_payload, "policy": "default"},
        )
        self.assertEqual(default_response.status_code, 200)
        self.assertEqual(default_response.json()["report"]["strategy"], "alias")

    async def test_manual_preview_creates_sqlite_session_store_file(self) -> None:
        payload = {
            "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
            "content_type": "text",
            "policy": "strict_token",
        }

        response = await self.client.post("/api/v1/mode/manual-preview", json=payload)

        self.assertEqual(response.status_code, 200)
        db_path = Path(os.environ["IPU_SESSION_STORE_PATH"])
        self.assertTrue(db_path.exists())
        self.assertGreater(db_path.stat().st_size, 0)

    async def test_manual_preview_restore_endpoint_restores_tokenized_text(self) -> None:
        preview_payload = {
            "content": "아이피유테크 홍길동 이사는 contact@ipu.co.kr 로 연락합니다.",
            "content_type": "text",
            "policy": "strict_token",
        }

        preview_response = await self.client.post("/api/v1/mode/manual-preview", json=preview_payload)
        self.assertEqual(preview_response.status_code, 200)
        preview_body = preview_response.json()
        self.assertTrue(preview_body["restore_token"])

        restore_response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": preview_body["session_id"],
                "restore_token": preview_body["restore_token"],
                "replaced_text": preview_body["replaced_text"],
            },
        )

        self.assertEqual(restore_response.status_code, 200)
        restore_body = restore_response.json()
        self.assertEqual(restore_body["session_id"], preview_body["session_id"])
        self.assertEqual(restore_body["restored_text"], preview_payload["content"])
        self.assertEqual(restore_body["restored"], True)

    async def test_manual_preview_restore_endpoint_rejects_missing_session(self) -> None:
        restore_response = await self.client.post(
            "/api/v1/mode/manual-preview/restore",
            json={
                "session_id": "missing-session",
                "restore_token": "missing-session-token",
                "replaced_text": "[EMAIL_01] 에 연락해 주세요.",
            },
        )

        self.assertEqual(restore_response.status_code, 403)

    def test_default_transcriber_is_placeholder(self) -> None:
        from app.core.settings import get_settings
        old_val = os.environ.pop("IPU_AUDIO_TRANSCRIBER", None)
        try:
            settings = get_settings()
            self.assertEqual(settings.audio_transcriber_kind, "placeholder")
        finally:
            if old_val is not None:
                os.environ["IPU_AUDIO_TRANSCRIBER"] = old_val


if __name__ == "__main__":
    unittest.main()


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

    offset = 0
    body = b""
    offsets = []
    for obj in objects:
        offsets.append(offset)
        body += obj
        offset += len(obj)

    xref_offset = len(body)
    xref_entries = [b"0000000000 65535 f \n"]
    xref_entries.extend(
        f"{item:010d} 00000 n \n".encode("ascii") for item in offsets
    )
    trailer = (
        b"xref\n0 "
        + str(len(objects) + 1).encode("ascii")
        + b"\n"
        + b"".join(xref_entries)
        + b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return b"%PDF-1.4\n" + body + trailer


def build_blank_pdf_bytes() -> bytes:
    return build_pdf_bytes([""])


def build_docx_bytes(paragraphs: list[str]) -> bytes:
    import zipfile

    document_xml = "".join(
        f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", f"<w:document><w:body>{document_xml}</w:body></w:document>")
    return buffer.getvalue()


def build_hwpx_bytes(sections: list[list[str]]) -> bytes:
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("mimetype", "application/hwp+zip")
        for index, paragraphs in enumerate(sections, start=1):
            text = "".join(f"<hp:p><hp:t>{item}</hp:t></hp:p>" for item in paragraphs)
            zf.writestr(f"Contents/section{index}.xml", text)
    return buffer.getvalue()


def build_wav_bytes(duration_seconds: float = 0.1) -> bytes:
    sample_rate = 8000
    frames = int(sample_rate * duration_seconds)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


class MissingOcrToolPdfFileParser:
    async def parse(self, file):
        raise ValueError("스캔형 PDF OCR을 위한 로컬 도구가 없습니다. tesseract 와 pdftoppm 설치 후 다시 시도해 주세요.")
