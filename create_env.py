#!/usr/bin/env python3
"""Secure .env file creator for ReconX Elite.

Reads GEMINI_API_KEY from system environment and creates .env file
without exposing secrets in logs or code.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from system environment variables."""
    project_root = Path(__file__).parent
    
    # Check if .env already exists
    env_file = project_root / ".env"
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return True
    
    # Read API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not found")
        print("Please set it first:")
        print("Windows: $env:GEMINI_API_KEY = 'your-api-key-here'")
        print("Linux/Mac: export GEMINI_API_KEY='your-api-key-here'")
        return False
    
    # Create .env file with only the API key
    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={api_key}\n")
        
        # Verify .gitignore contains .env
        gitignore_file = project_root / ".gitignore"
        gitignore_content = ""
        
        if gitignore_file.exists():
            with open(gitignore_file, "r", encoding="utf-8") as f:
                gitignore_content = f.read()
        
        if ".env" not in gitignore_content:
            with open(gitignore_file, "a", encoding="utf-8") as f:
                f.write("\n# Environment variables\n.env\n")
        
        print("✅ .env file created successfully")
        print("🔐 API key secured from environment variable")
        print("📝 .env added to .gitignore")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


if __name__ == "__main__":
    success = create_env_file()
    sys.exit(0 if success else 1)
