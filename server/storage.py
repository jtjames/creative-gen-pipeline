"""Dropbox storage helpers for the Creative Automation API."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

from config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class StorageArtifact:
    path: str


class DropboxStorage:
    """Thin wrapper around the Dropbox SDK for common storage operations."""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        if not self._settings.dropbox_access_token:
            raise RuntimeError("Dropbox access token is not configured. Set DROPBOX_ACCESS_TOKEN in the environment.")
        self._client = dropbox.Dropbox(self._settings.dropbox_access_token)

    @property
    def root_path(self) -> str:
        return self._settings.dropbox_root_path.rstrip("/") or "/"

    def _full_path(self, relative_path: str) -> str:
        relative = relative_path.strip()
        if not relative.startswith("/"):
            relative = f"/{relative}"
        if self.root_path == "/":
            return relative
        return f"{self.root_path}{relative}"

    def ensure_folder(self, path: str) -> str:
        """Ensure a folder exists, creating it when needed."""
        full_path = self._full_path(path)
        try:
            self._client.files_create_folder_v2(full_path)
        except ApiError as exc:
            error = exc.error
            if hasattr(error, "is_path") and error.is_path():
                path_error = error.get_path()
                if hasattr(path_error, "is_conflict") and path_error.is_conflict():
                    return full_path  # Folder already exists
            logger.error("Failed to ensure folder %s: %s", full_path, exc)
            raise RuntimeError("Unable to ensure Dropbox folder") from exc
        return full_path

    def upload_bytes(
        self,
        *,
        path: str,
        data: bytes,
        mode: WriteMode = WriteMode("overwrite"),
    ) -> StorageArtifact:
        """Upload raw bytes to Dropbox and return the artifact descriptor."""
        full_path = self._full_path(path)
        self._client.files_upload(data, full_path, mode=mode)
        return StorageArtifact(path=full_path)

    def delete_path(self, path: str) -> None:
        """Delete a path from Dropbox, ignoring missing entries."""
        full_path = self._full_path(path)
        try:
            self._client.files_delete_v2(full_path)
        except ApiError as exc:
            error = exc.error
            if hasattr(error, "is_path_lookup") and error.is_path_lookup():
                lookup = error.get_path_lookup()
                if hasattr(lookup, "is_not_found") and lookup.is_not_found():
                    logger.debug("Path already absent during delete: %s", full_path)
                    return
            logger.error("Failed to delete %s: %s", full_path, exc)
            raise RuntimeError("Unable to delete Dropbox path") from exc

    def list_paths(self, relative_folder: str = "") -> Iterable[str]:
        """Yield item paths within a folder relative to the configured root."""
        folder_path = self._full_path(relative_folder or "")
        list_path = folder_path if folder_path else "/"
        try:
            result = self._client.files_list_folder(list_path)
        except ApiError as exc:
            logger.error("Failed to list folder %s: %s", list_path, exc)
            raise RuntimeError("Unable to list Dropbox folder") from exc
        while True:
            for entry in result.entries:
                yield entry.path_lower
            if not result.has_more:
                break
            result = self._client.files_list_folder_continue(result.cursor)

    def generate_temporary_link(self, path: str) -> str:
        """Generate a temporary link for the given file path."""
        full_path = self._full_path(path)
        try:
            response = self._client.files_get_temporary_link(full_path)
        except ApiError as exc:
            logger.error("Failed to create temporary link for %s: %s", full_path, exc)
            raise RuntimeError("Unable to create temporary link") from exc
        return response.link
