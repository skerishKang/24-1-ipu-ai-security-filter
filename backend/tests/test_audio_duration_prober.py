from __future__ import annotations

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.exceptions import ProcessingLimitExceededError
from app.services.audio_transcriber import PlaceholderAudioTranscriber


class AudioDurationProberTest(unittest.TestCase):
    def test_non_wav_duration_probe_disabled_by_default(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch("app.services.audio_transcriber.subprocess.run") as run_mock:
            transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

        run_mock.assert_not_called()

    def test_ffprobe_missing_raises_clear_error(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch.dict("os.environ", {"IPU_AUDIO_DURATION_PROBER": "ffprobe"}):
            with patch("app.services.audio_transcriber.shutil.which", return_value=None):
                with self.assertRaises(ValueError) as ctx:
                    transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

        self.assertIn("ffprobe is required", str(ctx.exception))

    def test_ffprobe_allows_duration_under_limit(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch.dict("os.environ", {"IPU_AUDIO_DURATION_PROBER": "ffprobe"}):
            with patch("app.services.audio_transcriber.shutil.which", return_value="/usr/bin/ffprobe"):
                with patch(
                    "app.services.audio_transcriber.subprocess.run",
                    return_value=SimpleNamespace(stdout='{"format":{"duration":"12.5"}}'),
                ):
                    transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

    def test_ffprobe_rejects_duration_over_limit(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch.dict("os.environ", {"IPU_AUDIO_DURATION_PROBER": "ffprobe"}):
            with patch("app.services.audio_transcriber.shutil.which", return_value="/usr/bin/ffprobe"):
                with patch(
                    "app.services.audio_transcriber.subprocess.run",
                    return_value=SimpleNamespace(stdout='{"format":{"duration":"61.5"}}'),
                ):
                    with self.assertRaises(ProcessingLimitExceededError) as ctx:
                        transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

        self.assertIn("exceeds the processing limit", str(ctx.exception))

    def test_ffprobe_timeout_is_processing_limit_error(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch.dict("os.environ", {"IPU_AUDIO_DURATION_PROBER": "ffprobe"}):
            with patch("app.services.audio_transcriber.shutil.which", return_value="/usr/bin/ffprobe"):
                with patch(
                    "app.services.audio_transcriber.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(cmd=["ffprobe"], timeout=10),
                ):
                    with self.assertRaises(ProcessingLimitExceededError) as ctx:
                        transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

        self.assertIn("timeout", str(ctx.exception))

    def test_ffprobe_malformed_output_raises_clear_error(self) -> None:
        transcriber = PlaceholderAudioTranscriber()

        with patch.dict("os.environ", {"IPU_AUDIO_DURATION_PROBER": "ffprobe"}):
            with patch("app.services.audio_transcriber.shutil.which", return_value="/usr/bin/ffprobe"):
                with patch(
                    "app.services.audio_transcriber.subprocess.run",
                    return_value=SimpleNamespace(stdout='{"format":{"duration":"not-a-number"}}'),
                ):
                    with self.assertRaises(ValueError) as ctx:
                        transcriber._validate_non_wav_duration(b"audio-bytes", ".mp3")

        self.assertIn("invalid audio duration", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
