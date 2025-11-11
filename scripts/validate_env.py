#!/usr/bin/env python3
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
