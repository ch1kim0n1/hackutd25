#!/usr/bin/env python3
"""
Create Default Admin User
Creates a default admin user for initial login.
Username: admin
Password: admin123 (change immediately!)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from services.dao.json_dao import UserDAO
from services.security import PasswordService


def main():
    """Create default admin user."""
    user_dao = UserDAO()
    password_service = PasswordService()

    # Check if admin already exists
    existing = user_dao.get_user_by_username("admin")
    if existing:
        print("⚠️  Admin user already exists!")
        print("   Username: admin")
        print("   To reset password, delete data/users/")
        return 1

    # Create admin user
    user_data = {
        "username": "admin",
        "email": "admin@apex.local",
        "hashed_password": password_service.hash_password("admin123"),
        "is_active": True,
        "is_verified": True,
        "risk_tolerance": "moderate",
        "investment_experience": "intermediate"
    }

    try:
        user = user_dao.create_user(user_data)
        print("✅ Default admin user created successfully!")
        print()
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("   ⚠️  IMPORTANT: Change the password immediately after first login!")
        print()
        return 0

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
