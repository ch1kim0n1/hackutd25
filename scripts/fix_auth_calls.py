#!/usr/bin/env python3
"""
Helper script to remove manual authentication calls from server.py endpoints.
This script removes redundant get_current_user_from_request() calls since we now
use proper FastAPI dependency injection.
"""

import re
from pathlib import Path


def fix_auth_calls(file_path: Path):
    """Remove manual auth calls from endpoints that already use dependency injection."""

    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern 1: Remove "from middleware.auth import get_current_user_from_request" imports
    content = re.sub(
        r'\s*from middleware\.auth import get_current_user_from_request\s*\n',
        '\n',
        content
    )

    # Pattern 2: Remove manual auth calls like:
    # auth_data = await get_current_user_from_request(request)
    # user_id = auth_data['user_id']
    content = re.sub(
        r'\s*auth_data = await get_current_user_from_request\(request\)\s*\n\s*user_id = auth_data\[\'user_id\'\]\s*\n',
        '\n',
        content
    )

    # Pattern 3: Remove Request parameter if only used for auth
    # This is more conservative - only removes if Request is not used elsewhere in function
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a function definition with Request parameter
        if 'async def ' in line and 'Request' in line and 'current_user' in line:
            # Look ahead to see if Request is used elsewhere in the function
            function_body = []
            j = i + 1
            indent = len(line) - len(line.lstrip())

            # Collect function body
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() and not next_line.startswith(' ' * (indent + 1)):
                    break
                function_body.append(next_line)
                j += 1

            # Check if Request is used in the body (other than auth)
            request_used = any('request.' in body_line or 'request)' in body_line
                             for body_line in function_body
                             if 'get_current_user_from_request' not in body_line)

            # If Request is not used, remove it from parameters
            if not request_used and ', request: Request' in line:
                line = line.replace(', request: Request', '')
            elif not request_used and 'request: Request, ' in line:
                line = line.replace('request: Request, ', '')

        new_lines.append(line)
        i += 1

    content = '\n'.join(new_lines)

    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True

    return False


def main():
    """Main function to fix auth calls in server.py"""
    server_path = Path('src/backend/server.py')

    if not server_path.exists():
        print(f"Error: {server_path} not found!")
        print("Please run this script from the project root directory.")
        return 1

    print(f"Fixing authentication calls in {server_path}...")

    if fix_auth_calls(server_path):
        print("✅ Successfully removed redundant authentication calls!")
        print("\nChanges made:")
        print("- Removed 'from middleware.auth import get_current_user_from_request' imports")
        print("- Removed manual 'auth_data = await get_current_user_from_request(request)' calls")
        print("- Removed 'user_id = auth_data['user_id']' lines")
        print("- Removed unused Request parameters where applicable")
        print("\nNote: The endpoints now properly use the 'current_user' parameter from dependency injection.")
    else:
        print("ℹ️  No changes needed - file is already clean!")

    return 0


if __name__ == '__main__':
    exit(main())
