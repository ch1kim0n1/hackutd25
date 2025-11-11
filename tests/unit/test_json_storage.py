"""
Unit tests for JSON Storage Service.
Tests local JSON file-based storage operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "backend"))

from services.json_storage_service import JSONStorage, StorageManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for test storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def json_storage(temp_storage_dir):
    """Create a JSONStorage instance for testing."""
    return JSONStorage("test_users", base_path=temp_storage_dir)


class TestJSONStorage:
    """Test JSONStorage class."""

    def test_create_entity(self, json_storage):
        """Test creating a new entity."""
        entity_data = {
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True
        }

        result = json_storage.create("user_123", entity_data)

        assert result["id"] == "user_123"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert "created_at" in result
        assert "updated_at" in result

    def test_create_duplicate_entity(self, json_storage):
        """Test that creating a duplicate entity raises an error."""
        entity_data = {"username": "testuser"}

        json_storage.create("user_123", entity_data)

        with pytest.raises(ValueError, match="already exists"):
            json_storage.create("user_123", entity_data)

    def test_read_entity(self, json_storage):
        """Test reading an existing entity."""
        entity_data = {"username": "testuser"}
        json_storage.create("user_123", entity_data)

        result = json_storage.read("user_123")

        assert result is not None
        assert result["id"] == "user_123"
        assert result["username"] == "testuser"

    def test_read_nonexistent_entity(self, json_storage):
        """Test reading a non-existent entity returns None."""
        result = json_storage.read("nonexistent")
        assert result is None

    def test_update_entity(self, json_storage):
        """Test updating an existing entity."""
        entity_data = {"username": "testuser", "email": "old@example.com"}
        json_storage.create("user_123", entity_data)

        update_data = {"email": "new@example.com"}
        result = json_storage.update("user_123", update_data)

        assert result is not None
        assert result["email"] == "new@example.com"
        assert result["username"] == "testuser"  # Original data preserved

    def test_update_nonexistent_entity(self, json_storage):
        """Test updating a non-existent entity returns None."""
        result = json_storage.update("nonexistent", {"email": "test@example.com"})
        assert result is None

    def test_delete_entity(self, json_storage):
        """Test deleting an entity."""
        entity_data = {"username": "testuser"}
        json_storage.create("user_123", entity_data)

        result = json_storage.delete("user_123")
        assert result is True

        # Verify it's deleted
        assert json_storage.read("user_123") is None

    def test_delete_nonexistent_entity(self, json_storage):
        """Test deleting a non-existent entity returns False."""
        result = json_storage.delete("nonexistent")
        assert result is False

    def test_list_all_entities(self, json_storage):
        """Test listing all entity IDs."""
        json_storage.create("user_1", {"username": "user1"})
        json_storage.create("user_2", {"username": "user2"})
        json_storage.create("user_3", {"username": "user3"})

        entity_ids = json_storage.list_all()

        assert len(entity_ids) == 3
        assert "user_1" in entity_ids
        assert "user_2" in entity_ids
        assert "user_3" in entity_ids

    def test_find_entities(self, json_storage):
        """Test finding entities with a filter function."""
        json_storage.create("user_1", {"username": "alice", "age": 25})
        json_storage.create("user_2", {"username": "bob", "age": 30})
        json_storage.create("user_3", {"username": "charlie", "age": 25})

        # Find users with age 25
        results = json_storage.find(lambda e: e.get("age") == 25)

        assert len(results) == 2
        usernames = [r["username"] for r in results]
        assert "alice" in usernames
        assert "charlie" in usernames

    def test_find_one_entity(self, json_storage):
        """Test finding the first entity matching a filter."""
        json_storage.create("user_1", {"username": "alice", "role": "admin"})
        json_storage.create("user_2", {"username": "bob", "role": "user"})

        result = json_storage.find_one(lambda e: e.get("role") == "admin")

        assert result is not None
        assert result["username"] == "alice"

    def test_find_one_no_match(self, json_storage):
        """Test finding when no entity matches the filter."""
        json_storage.create("user_1", {"username": "alice", "role": "user"})

        result = json_storage.find_one(lambda e: e.get("role") == "admin")
        assert result is None

    def test_backup_creation(self, json_storage):
        """Test that backups are created on updates."""
        json_storage.create("user_1", {"username": "testuser"})
        json_storage.update("user_1", {"username": "updated"})

        backup_dir = json_storage.backup_path
        backup_files = list(backup_dir.glob("user_1_*.json"))

        assert len(backup_files) >= 1


class TestStorageManager:
    """Test StorageManager class."""

    def test_get_storage_creates_instance(self, temp_storage_dir):
        """Test that get_storage creates a new instance if needed."""
        manager = StorageManager(base_path=temp_storage_dir)

        storage = manager.get_storage("users")

        assert isinstance(storage, JSONStorage)
        assert storage.entity_type == "users"

    def test_get_storage_returns_same_instance(self, temp_storage_dir):
        """Test that get_storage returns the same instance for same entity type."""
        manager = StorageManager(base_path=temp_storage_dir)

        storage1 = manager.get_storage("users")
        storage2 = manager.get_storage("users")

        assert storage1 is storage2

    def test_property_accessors(self, temp_storage_dir):
        """Test property accessors for common entity types."""
        manager = StorageManager(base_path=temp_storage_dir)

        assert isinstance(manager.users, JSONStorage)
        assert isinstance(manager.portfolios, JSONStorage)
        assert isinstance(manager.trades, JSONStorage)
        assert isinstance(manager.goals, JSONStorage)

    def test_thread_safety(self, json_storage):
        """Test that concurrent operations are thread-safe."""
        import threading

        def create_entity(entity_id):
            try:
                json_storage.create(entity_id, {"data": entity_id})
            except ValueError:
                pass  # Ignore duplicate errors

        threads = [
            threading.Thread(target=create_entity, args=(f"user_{i}",))
            for i in range(10)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All entities should be created successfully
        entity_ids = json_storage.list_all()
        assert len(entity_ids) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
