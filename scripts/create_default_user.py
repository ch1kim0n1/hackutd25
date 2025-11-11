#!/usr/bin/env python3
"""
Create Default Admin User Script
Creates a default admin user for initial system access.

Default Credentials:
  Username: admin
  Password: admin123
  Email: admin@apex.local

⚠️  SECURITY: Change the password immediately after first login!
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from services.dao.json_dao import UserDAO
from services.security.password_service import PasswordService


def main():
    """Create default admin user if it doesn't already exist."""

    # Default credentials
    default_username = "admin"
    default_email = "admin@apex.local"
    default_password = "admin123"

    print("=" * 60)
    print("APEX Default Admin User Creation")
    print("=" * 60)

    try:
        user_dao = UserDAO()
        password_service = PasswordService()

        # Check if admin user already exists
        existing_user = user_dao.get_user_by_username(default_username)
        if existing_user:
            print(f"✅ Admin user '{default_username}' already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print()
            print("⚠️  If you've forgotten the password, you can reset it by:")
            print("   1. Deleting the user from data/users.json")
            print("   2. Running this script again")
            print()
            return 0

        # Create admin user
        print(f"Creating admin user '{default_username}'...")

        hashed_password = password_service.hash_password(default_password)

        user_data = {
            "username": default_username,
            "email": default_email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_verified": True,
            "risk_tolerance": "moderate",
            "investment_experience": "advanced"
        }

        user = user_dao.create_user(user_data)

        print("✅ Admin user created successfully!")
        print()
        print("=" * 60)
        print("Default Admin Credentials")
        print("=" * 60)
        print(f"Username: {default_username}")
        print(f"Password: {default_password}")
        print(f"Email:    {default_email}")
        print(f"User ID:  {user.id}")
        print("=" * 60)
        print()
        print("⚠️  SECURITY WARNING:")
        print("   Please change the default password after first login!")
        print("   This is a well-known default credential.")
        print()
        print("🔐 To login:")
        print("   1. Start the backend: cd src/backend && python3 server.py")
        print("   2. POST to /auth/login with credentials above")
        print("   3. Use the returned JWT token for authenticated requests")
        print()
        return 0

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
