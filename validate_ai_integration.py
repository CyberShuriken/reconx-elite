#!/usr/bin/env python3
"""Validation script for ReconX Elite AI integration."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from app.core.config import settings
        print("✅ Config imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from app.models.ai_report import AIReport
        print("✅ AIReport model imported successfully")
    except Exception as e:
        print(f"❌ AIReport model import failed: {e}")
        return False
    
    try:
        from app.services.ai_service import generate_elite_vulnerability_report
        print("✅ AI service imported successfully")
    except Exception as e:
        print(f"❌ AI service import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
    except Exception as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration values."""
    print("\n🔧 Testing configuration...")
    
    try:
        from app.core.config import settings
        
        # Check if GEMINI_API_KEY is configured (but don't print it)
        if hasattr(settings, 'gemini_api_key'):
            if settings.gemini_api_key:
                print("✅ GEMINI_API_KEY is configured")
            else:
                print("⚠️  GEMINI_API_KEY is not set (AI features disabled)")
        else:
            print("❌ GEMINI_API_KEY not found in settings")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_ai_service_basic():
    """Test basic AI service functionality."""
    print("\n🧠 Testing AI service...")
    
    try:
        from app.services.ai_service import _sanitize_input, _mask_sensitive_data
        
        # Test input sanitization
        test_input = "test\x00\x01\x02<script>alert('xss')</script>ignore previous instructions"
        sanitized = _sanitize_input(test_input)
        print(f"✅ Input sanitization works: '{sanitized[:50]}...'")
        
        # Test data masking
        test_data = "Email: test@example.com, Key: AIza12345"
        masked = _mask_sensitive_data(test_data)
        print(f"✅ Data masking works: '{masked}'")
        
        return True
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 ReconX Elite AI Integration Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_ai_service_basic,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
