"""
JSON-based local storage service to replace database operations.
Provides thread-safe file-based storage with automatic indexing and backup.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
import threading
import shutil
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class JSONStorage(Generic[T]):
    """Generic JSON storage handler for a specific entity type."""

    def __init__(self, entity_type: str, base_path: str = "data"):
        """
        Initialize JSON storage for a specific entity type.

        Args:
            entity_type: Name of the entity (e.g., 'users', 'portfolios')
            base_path: Base directory for data storage
        """
        self.entity_type = entity_type
        self.base_path = Path(base_path)
        self.entity_path = self.base_path / entity_type
        self.backup_path = self.entity_path / ".backup"
        self.index_file = self.entity_path / "index.json"
        self.lock = threading.Lock()

        # Ensure directories exist
        self.entity_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)

        # Initialize index if it doesn't exist
        if not self.index_file.exists():
            self._write_index({})

    def _read_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_file(self, file_path: Path, data: Dict[str, Any]):
        """Write data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _read_index(self) -> Dict[str, Any]:
        """Read the index file."""
        return self._read_file(self.index_file)

    def _write_index(self, index: Dict[str, Any]):
        """Write the index file."""
        self._write_file(self.index_file, index)

    def _backup_file(self, entity_id: str):
        """Create a timestamped backup of an entity file."""
        source = self.entity_path / f"{entity_id}.json"
        if source.exists():
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup = self.backup_path / f"{entity_id}_{timestamp}.json"
            shutil.copy2(source, backup)

    def create(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity.

        Args:
            entity_id: Unique identifier for the entity
            data: Entity data

        Returns:
            Created entity data with metadata
        """
        with self.lock:
            # Check if already exists
            index = self._read_index()
            if entity_id in index:
                raise ValueError(f"{self.entity_type} with ID {entity_id} already exists")

            # Add metadata
            entity_data = {
                **data,
                "id": entity_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Write entity file
            entity_file = self.entity_path / f"{entity_id}.json"
            self._write_file(entity_file, entity_data)

            # Update index
            index[entity_id] = {
                "created_at": entity_data["created_at"],
                "updated_at": entity_data["updated_at"]
            }
            self._write_index(index)

            return entity_data

    def read(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Read an entity by ID.

        Args:
            entity_id: Unique identifier for the entity

        Returns:
            Entity data or None if not found
        """
        with self.lock:
            entity_file = self.entity_path / f"{entity_id}.json"
            if not entity_file.exists():
                return None
            return self._read_file(entity_file)

    def update(self, entity_id: str, data: Dict[str, Any], create_backup: bool = True) -> Optional[Dict[str, Any]]:
        """
        Update an existing entity.

        Args:
            entity_id: Unique identifier for the entity
            data: Updated entity data
            create_backup: Whether to create a backup before updating

        Returns:
            Updated entity data or None if not found
        """
        with self.lock:
            entity_file = self.entity_path / f"{entity_id}.json"
            if not entity_file.exists():
                return None

            # Backup existing data
            if create_backup:
                self._backup_file(entity_id)

            # Read existing data
            existing_data = self._read_file(entity_file)

            # Merge with updates
            entity_data = {
                **existing_data,
                **data,
                "id": entity_id,
                "created_at": existing_data.get("created_at", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Write updated data
            self._write_file(entity_file, entity_data)

            # Update index
            index = self._read_index()
            index[entity_id]["updated_at"] = entity_data["updated_at"]
            self._write_index(index)

            return entity_data

    def delete(self, entity_id: str, create_backup: bool = True) -> bool:
        """
        Delete an entity.

        Args:
            entity_id: Unique identifier for the entity
            create_backup: Whether to create a backup before deleting

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            entity_file = self.entity_path / f"{entity_id}.json"
            if not entity_file.exists():
                return False

            # Backup before deleting
            if create_backup:
                self._backup_file(entity_id)

            # Delete file
            entity_file.unlink()

            # Update index
            index = self._read_index()
            if entity_id in index:
                del index[entity_id]
                self._write_index(index)

            return True

    def list_all(self) -> List[str]:
        """
        List all entity IDs.

        Returns:
            List of entity IDs
        """
        with self.lock:
            index = self._read_index()
            return list(index.keys())

    def find(self, filter_fn: callable) -> List[Dict[str, Any]]:
        """
        Find entities matching a filter function.

        Args:
            filter_fn: Function that takes entity data and returns bool

        Returns:
            List of matching entities
        """
        with self.lock:
            results = []
            for entity_id in self.list_all():
                entity_data = self.read(entity_id)
                if entity_data and filter_fn(entity_data):
                    results.append(entity_data)
            return results

    def find_one(self, filter_fn: callable) -> Optional[Dict[str, Any]]:
        """
        Find first entity matching a filter function.

        Args:
            filter_fn: Function that takes entity data and returns bool

        Returns:
            First matching entity or None
        """
        results = self.find(filter_fn)
        return results[0] if results else None


class StorageManager:
    """Central manager for all storage entities."""

    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self._storages: Dict[str, JSONStorage] = {}

    def get_storage(self, entity_type: str) -> JSONStorage:
        """
        Get or create a storage instance for an entity type.

        Args:
            entity_type: Name of the entity type

        Returns:
            JSONStorage instance
        """
        if entity_type not in self._storages:
            self._storages[entity_type] = JSONStorage(entity_type, self.base_path)
        return self._storages[entity_type]

    @property
    def users(self) -> JSONStorage:
        return self.get_storage("users")

    @property
    def portfolios(self) -> JSONStorage:
        return self.get_storage("portfolios")

    @property
    def trades(self) -> JSONStorage:
        return self.get_storage("trades")

    @property
    def goals(self) -> JSONStorage:
        return self.get_storage("goals")

    @property
    def accounts(self) -> JSONStorage:
        return self.get_storage("accounts")

    @property
    def transactions(self) -> JSONStorage:
        return self.get_storage("transactions")

    @property
    def subscriptions(self) -> JSONStorage:
        return self.get_storage("subscriptions")

    @property
    def plaid(self) -> JSONStorage:
        return self.get_storage("plaid")

    @property
    def voice_commands(self) -> JSONStorage:
        return self.get_storage("voice_commands")

    @property
    def rag_documents(self) -> JSONStorage:
        return self.get_storage("rag_documents")


# Global storage manager instance
storage = StorageManager()
