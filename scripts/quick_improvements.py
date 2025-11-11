#!/usr/bin/env python3
"""
Quick Improvements Script
Implements several quick wins identified in the project re-evaluation.
Run this script to automatically improve the codebase.
"""

import os
import sys
import shutil
from pathlib import Path


def remove_alembic():
    """Remove obsolete Alembic directory."""
    alembic_path = Path("src/backend/alembic")
    if alembic_path.exists():
        print("🗑️  Removing obsolete Alembic directory...")
        shutil.rmtree(alembic_path)
        print("   ✅ Removed src/backend/alembic/")
    else:
        print("   ℹ️  Alembic directory already removed")


def create_logs_directory():
    """Create logs directory for file logging."""
    logs_path = Path("logs")
    if not logs_path.exists():
        print("📁 Creating logs directory...")
        logs_path.mkdir()
        print("   ✅ Created logs/")

        # Create .gitignore for logs
        gitignore = logs_path / ".gitignore"
        gitignore.write_text("*\n!.gitignore\n")
        print("   ✅ Created logs/.gitignore")
    else:
        print("   ℹ️  Logs directory already exists")


def create_backups_directory():
    """Create backups directory for data backups."""
    backups_path = Path("backups")
    if not backups_path.exists():
        print("📁 Creating backups directory...")
        backups_path.mkdir()
        print("   ✅ Created backups/")

        # Create .gitignore for backups
        gitignore = backups_path / ".gitignore"
        gitignore.write_text("*\n!.gitignore\n")
        print("   ✅ Created backups/.gitignore")
    else:
        print("   ℹ️  Backups directory already exists")


def create_default_user_script():
    """Create script to generate default admin user."""
    script_path = Path("scripts/create_default_user.py")

    if script_path.exists():
        print("   ℹ️  Default user script already exists")
        return

    print("📝 Creating default user creation script...")

    script_content = '''#!/usr/bin/env python3
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
'''

    script_path.write_text(script_content)
    os.chmod(script_path, 0o755)
    print("   ✅ Created scripts/create_default_user.py")


def create_health_check():
    """Add health check endpoint to server.py"""
    server_path = Path("src/backend/server.py")

    if not server_path.exists():
        print("   ⚠️  server.py not found, skipping health check")
        return

    content = server_path.read_text()

    # Check if health check already exists
    if "/health" in content:
        print("   ℹ️  Health check endpoint already exists")
        return

    print("🏥 Adding health check endpoint...")

    # Find a good place to add it (after imports, before first endpoint)
    health_check_code = '''

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Returns server status and basic diagnostics.
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "storage": "ok",
            "authentication": "ok"
        }
    }
'''

    # Find the app creation and add after it
    if 'app = FastAPI(' in content:
        parts = content.split('app = FastAPI(', 1)
        # Find the closing of the FastAPI() call
        closing_idx = parts[1].find(')')
        before = parts[0] + 'app = FastAPI(' + parts[1][:closing_idx+1]

        # Skip any middleware setup
        rest = parts[1][closing_idx+1:]
        # Find first @app decorator
        first_endpoint = rest.find('@app.')

        if first_endpoint != -1:
            new_content = before + rest[:first_endpoint] + health_check_code + '\n' + rest[first_endpoint:]
            server_path.write_text(new_content)
            print("   ✅ Added /health endpoint to server.py")
        else:
            print("   ⚠️  Could not find appropriate location, skipping")
    else:
        print("   ⚠️  Could not find FastAPI app initialization, skipping")


def add_env_validation():
    """Add environment variable validation"""
    print("🔐 Adding environment variable validation...")

    validation_code = '''#!/usr/bin/env python3
"""
Environment Variable Validator
Run this before starting the backend to ensure all required variables are set.
"""

import os
import sys


def validate_env():
    """Validate required environment variables."""

    required_vars = {
        "JWT_SECRET_KEY": "JWT secret for authentication",
        "ALPACA_API_KEY": "Alpaca trading API key",
        "ALPACA_SECRET_KEY": "Alpaca trading secret key",
    }

    recommended_vars = {
        "OPENAI_API_KEY": "OpenAI API key (for AI features)",
        "ANTHROPIC_API_KEY": "Anthropic API key (for Claude)",
        "ENCRYPTION_KEY": "Credential encryption key",
    }

    print("🔍 Validating environment variables...")
    print()

    missing_required = []
    missing_recommended = []

    # Check required
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append((var, description))
            print(f"   ❌ {var} - {description}")
        else:
            print(f"   ✅ {var}")

    # Check recommended
    for var, description in recommended_vars.items():
        value = os.getenv(var)
        if not value:
            missing_recommended.append((var, description))
            print(f"   ⚠️  {var} - {description} (optional)")
        else:
            print(f"   ✅ {var}")

    print()

    if missing_required:
        print("❌ Missing required environment variables!")
        print()
        print("Please set the following variables in your .env file:")
        for var, desc in missing_required:
            print(f"   {var}={desc}")
        print()
        print("Copy .env.example to .env and fill in your values:")
        print("   cp .env.example .env")
        print()
        return False

    if missing_recommended:
        print("⚠️  Some recommended variables are missing.")
        print("   The application will work but some features may be unavailable.")
        print()

    print("✅ Environment validation complete!")
    return True


if __name__ == "__main__":
    if not validate_env():
        sys.exit(1)
'''

    validator_path = Path("scripts/validate_env.py")
    validator_path.write_text(validation_code)
    os.chmod(validator_path, 0o755)
    print("   ✅ Created scripts/validate_env.py")


def main():
    """Run all quick improvements."""
    print("=" * 60)
    print(" APEX Quick Improvements")
    print("=" * 60)
    print()

    # Check we're in the right directory
    if not Path("src/backend").exists():
        print("❌ Error: Must run from project root directory")
        print("   Current directory:", os.getcwd())
        return 1

    try:
        remove_alembic()
        create_logs_directory()
        create_backups_directory()
        create_default_user_script()
        add_env_validation()
        create_health_check()

        print()
        print("=" * 60)
        print(" ✅ Quick improvements complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: python scripts/create_default_user.py")
        print("  2. Run: python scripts/validate_env.py")
        print("  3. Start backend: cd src/backend && python server.py")
        print()

        return 0

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
