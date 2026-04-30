"""
Custom exception types for the app package.
"""


class ReleaseBlockedError(Exception):
    """Raised when a release attempt is blocked by a policy layer.

    Attributes:
        message: Human-readable description of the blocking reason.
        details: Structured dict with additional context (e.g. gate results,
            governance decision).
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"ReleaseBlockedError({self.message!r}, details={self.details!r})"
