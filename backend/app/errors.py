from typing import Any


class DomainError(Exception):
    def __init__(self, status_code: int, message: str, details: Any | None = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)
