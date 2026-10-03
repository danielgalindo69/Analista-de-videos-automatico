"""Process-local secret storage for bring-your-own-key providers."""

from threading import RLock


class SessionCredentialStore:
    """
    Keeps credentials only in backend memory.

    Credentials are intentionally lost when the process or Docker container
    restarts. Persistent encrypted storage belongs to a later desktop/runtime
    integration and must not be emulated with browser storage.
    """

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._lock = RLock()

    def set(self, provider_id: str, credential: str) -> None:
        value = credential.strip()
        if not value:
            raise ValueError("Credential cannot be empty")
        with self._lock:
            self._values[provider_id] = value

    def get(self, provider_id: str) -> str | None:
        with self._lock:
            return self._values.get(provider_id)

    def has(self, provider_id: str) -> bool:
        with self._lock:
            return provider_id in self._values

    def delete(self, provider_id: str) -> None:
        with self._lock:
            self._values.pop(provider_id, None)
