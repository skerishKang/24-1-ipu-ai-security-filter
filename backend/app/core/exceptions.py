"""Custom exceptions for IPU AI Firewall."""


class FileTooLargeError(ValueError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size_mb: int = 100) -> None:
        self.max_size_mb = max_size_mb
        super().__init__(f"파일 크기가 {max_size_mb}MB를 초과합니다.")


class EmptyFileError(ValueError):
    """Raised when uploaded file is empty."""

    def __init__(self) -> None:
        super().__init__("비어 있는 파일은 업로드할 수 없습니다.")


class UnsupportedFileTypeError(ValueError):
    """Raised when file type is not supported."""

    def __init__(self, supported_types: str) -> None:
        self.supported_types = supported_types
        super().__init__(f"지원하지 않는 파일 형식입니다. {supported_types}만 지원합니다.")


class InvalidEncodingError(ValueError):
    """Raised when file encoding is invalid."""

    def __init__(self) -> None:
        super().__init__("UTF-8 텍스트 파일만 지원합니다.")


class AudioTranscriptionError(Exception):
    """Raised when audio transcription fails."""



class SessionExpiredError(KeyError):
    """Raised when session has expired."""

    def __init__(self) -> None:
        super().__init__("세션이 만료되었습니다.")


class RestoreTokenError(PermissionError):
    """Raised when restore token validation fails."""

    def __init__(self) -> None:
        super().__init__("복원 권한을 확인할 수 없습니다.")


class ProcessingLimitExceededError(ValueError):
    """Raised when a processing limit is exceeded (pages, OCR, timeout)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
