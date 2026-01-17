"""
Validation script to verify the setup is correct.
Run this after installing dependencies and configuring .env
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor} (requires 3.10+)")
        return False


def check_dependencies():
    """Check if key dependencies are installed"""
    print("\nChecking dependencies...")
    required = [
        ("google.generativeai", "google-generativeai"),
        ("sentence_transformers", "sentence-transformers"),
        ("chromadb", "chromadb"),
        ("streamlit", "streamlit"),
        ("pydantic", "pydantic"),
        ("dotenv", "python-dotenv"),
        ("requests", "requests"),
        ("spacy", "spacy"),
    ]

    all_installed = True
    for module, package in required:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (not installed)")
            all_installed = False

    return all_installed


def check_env_file():
    """Check if .env file exists"""
    print("\nChecking .env file...")
    env_path = Path(".env")
    if env_path.exists():
        print(f"  ✅ .env file exists")

        # Check for API key
        with open(env_path) as f:
            content = f.read()
            if "GEMINI_API_KEY=" in content and "your_api_key_here" not in content:
                print(f"  ✅ GEMINI_API_KEY is configured")
                return True
            else:
                print(f"  ⚠️  GEMINI_API_KEY not set (edit .env)")
                return False
    else:
        print(f"  ❌ .env file not found (copy from .env.example)")
        return False


def check_directory_structure():
    """Check if all directories exist"""
    print("\nChecking directory structure...")
    required_dirs = [
        "config",
        "src/core",
        "src/knowledge_base",
        "src/api",
        "src/rag",
        "src/agent",
        "src/utils",
        "data/knowledge_base/raw",
        "data/chromadb",
        "data/sqlite",
        "streamlit_app/components",
        "scripts",
        "tests/unit",
        "tests/integration",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (missing)")
            all_exist = False

    return all_exist


def test_imports():
    """Test importing core modules"""
    print("\nTesting core module imports...")

    try:
        from config.settings import settings
        print(f"  ✅ config.settings")

        from config.prompts import SYSTEM_PROMPT
        print(f"  ✅ config.prompts")

        from config.api_config import ENDPOINTS
        print(f"  ✅ config.api_config")

        from src.core.embeddings import get_embedding_manager
        print(f"  ✅ src.core.embeddings")

        from src.core.llm_client import get_gemini_client
        print(f"  ✅ src.core.llm_client")

        from src.core.cache_manager import get_cache_manager
        print(f"  ✅ src.core.cache_manager")

        from src.utils.logging_config import logger
        print(f"  ✅ src.utils.logging_config")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_embedding_manager():
    """Test embedding manager functionality"""
    print("\nTesting embedding manager...")
    try:
        from src.core.embeddings import get_embedding_manager

        emb_mgr = get_embedding_manager()
        embedding = emb_mgr.embed_text("Test sentence")

        if len(embedding) == 384:
            print(f"  ✅ Embedding generated (dimension: {len(embedding)})")
            return True
        else:
            print(f"  ❌ Unexpected embedding dimension: {len(embedding)}")
            return False
    except Exception as e:
        print(f"  ❌ Embedding test failed: {e}")
        return False


def test_cache_manager():
    """Test cache manager functionality"""
    print("\nTesting cache manager...")
    try:
        from src.core.cache_manager import get_cache_manager

        cache = get_cache_manager()

        # Test set/get
        cache.set("test_endpoint", {"param": "value"}, {"result": "data"}, ttl=60)
        cached = cache.get("test_endpoint", {"param": "value"})

        if cached == {"result": "data"}:
            print(f"  ✅ Cache set/get working")

            # Get stats
            stats = cache.get_stats()
            print(f"  ✅ Cache stats: {stats['active_entries']} active entries")
            return True
        else:
            print(f"  ❌ Cache test failed")
            return False
    except Exception as e:
        print(f"  ❌ Cache test failed: {e}")
        return False


def test_gemini_client():
    """Test Gemini client (requires API key)"""
    print("\nTesting Gemini client...")
    try:
        from src.core.llm_client import get_gemini_client

        client = get_gemini_client()

        # Test with simple prompt
        response = client.generate("Say 'Hello' in one word")

        if response and len(response) > 0:
            print(f"  ✅ Gemini API working (response: '{response[:50]}...')")
            return True
        else:
            print(f"  ❌ Empty response from Gemini")
            return False
    except Exception as e:
        print(f"  ⚠️  Gemini test failed (check API key): {e}")
        return False


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Crypto Agent Setup Validation")
    print("=" * 60)

    results = []

    # Basic checks
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Environment File", check_env_file()))
    results.append(("Directory Structure", check_directory_structure()))

    # Module tests
    results.append(("Core Imports", test_imports()))
    results.append(("Embedding Manager", test_embedding_manager()))
    results.append(("Cache Manager", test_cache_manager()))
    results.append(("Gemini Client", test_gemini_client()))

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All checks passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Proceed to Phase 3: Create knowledge base data")
        print("2. Run: python scripts/init_kb.py (after implementing Phase 3)")
        print("3. Continue with remaining phases")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon issues:")
        print("- Missing dependencies: pip install -r requirements.txt")
        print("- Missing .env: cp .env.example .env")
        print("- Missing API key: Add GEMINI_API_KEY to .env")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
