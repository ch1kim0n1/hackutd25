#!/usr/bin/env python3
"""
Data Backup Script
Creates timestamped backups of the entire data directory.

Usage:
    python3 scripts/backup_data.py              # Create backup
    python3 scripts/backup_data.py --list       # List backups
    python3 scripts/backup_data.py --restore <timestamp>  # Restore backup
"""

import sys
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import json


class BackupManager:
    """Manages data directory backups"""

    def __init__(self, data_dir: str = "data", backup_dir: str = "backups"):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> Path:
        """
        Create a timestamped backup of the data directory.

        Returns:
            Path to the created backup
        """
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

        # Generate timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"data_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        print(f"Creating backup: {backup_name}")
        print(f"Source: {self.data_dir}")
        print(f"Destination: {backup_path}")

        # Create backup
        shutil.copytree(self.data_dir, backup_path)

        # Create metadata file
        metadata = {
            "timestamp": timestamp,
            "created_at": datetime.utcnow().isoformat(),
            "source": str(self.data_dir),
            "backup_path": str(backup_path),
        }

        metadata_path = backup_path / "backup_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Calculate size
        total_size = sum(
            f.stat().st_size for f in backup_path.rglob('*') if f.is_file()
        )
        size_mb = total_size / (1024 * 1024)

        print(f"✅ Backup created successfully!")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Location: {backup_path}")

        return backup_path

    def list_backups(self) -> list:
        """
        List all available backups.

        Returns:
            List of backup paths sorted by timestamp (newest first)
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_dir() and backup_path.name.startswith("data_backup_"):
                metadata_path = backup_path / "backup_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    backups.append({
                        "path": backup_path,
                        "timestamp": metadata.get("timestamp", "unknown"),
                        "created_at": metadata.get("created_at", "unknown"),
                    })
                else:
                    # Backup without metadata
                    backups.append({
                        "path": backup_path,
                        "timestamp": backup_path.name.replace("data_backup_", ""),
                        "created_at": "unknown",
                    })

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)

        return backups

    def restore_backup(self, timestamp: str, confirm: bool = False) -> bool:
        """
        Restore a backup by timestamp.

        Args:
            timestamp: Timestamp of the backup to restore
            confirm: If True, skip confirmation prompt

        Returns:
            True if restore successful, False otherwise
        """
        backup_name = f"data_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False

        # Confirm restoration
        if not confirm:
            print(f"⚠️  WARNING: This will replace the current data directory!")
            print(f"   Current: {self.data_dir}")
            print(f"   Backup: {backup_path}")
            response = input("\nContinue? (yes/no): ").strip().lower()
            if response != "yes":
                print("Restore cancelled.")
                return False

        # Create backup of current data before restoring
        if self.data_dir.exists():
            current_backup_name = f"data_backup_pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            current_backup_path = self.backup_dir / current_backup_name
            print(f"Creating safety backup of current data: {current_backup_name}")
            shutil.copytree(self.data_dir, current_backup_path)

        # Remove current data directory
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

        # Restore backup
        print(f"Restoring backup: {backup_name}")
        shutil.copytree(backup_path, self.data_dir)

        print("✅ Backup restored successfully!")
        return True

    def cleanup_old_backups(self, keep_count: int = 10):
        """
        Remove old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of recent backups to keep
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            print(f"No cleanup needed. {len(backups)} backups found (keeping {keep_count})")
            return

        to_delete = backups[keep_count:]

        print(f"Removing {len(to_delete)} old backups (keeping {keep_count} most recent)")

        for backup in to_delete:
            backup_path = backup["path"]
            print(f"   Deleting: {backup_path.name}")
            shutil.rmtree(backup_path)

        print(f"✅ Cleanup complete! Kept {keep_count} most recent backups.")


def main():
    parser = argparse.ArgumentParser(description="APEX Data Backup Manager")
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available backups"
    )
    parser.add_argument(
        "--restore", "-r",
        metavar="TIMESTAMP",
        help="Restore backup by timestamp (e.g., 20250111_143000)"
    )
    parser.add_argument(
        "--cleanup", "-c",
        type=int,
        metavar="KEEP_COUNT",
        help="Remove old backups, keeping only N most recent"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    backup_manager = BackupManager()

    try:
        if args.list:
            # List backups
            backups = backup_manager.list_backups()

            if not backups:
                print("No backups found.")
                return 0

            print("=" * 60)
            print("Available Backups")
            print("=" * 60)

            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['timestamp']}")
                print(f"   Created: {backup['created_at']}")
                print(f"   Path: {backup['path']}")
                print()

            return 0

        elif args.restore:
            # Restore backup
            success = backup_manager.restore_backup(args.restore, confirm=args.yes)
            return 0 if success else 1

        elif args.cleanup:
            # Cleanup old backups
            backup_manager.cleanup_old_backups(keep_count=args.cleanup)
            return 0

        else:
            # Create backup (default action)
            print("=" * 60)
            print("APEX Data Backup")
            print("=" * 60)
            backup_manager.create_backup()
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
