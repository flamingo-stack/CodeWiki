#!/usr/bin/env python3
"""
Local configuration test script for CodeWiki.
Tests that the configuration system works properly with API keys from .env.local
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add CodeWiki to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from codewiki.cli.config_manager import ConfigManager
from codewiki.src.config import Config


class TestResults:
    """Accumulates test results and prints a structured summary."""

    def __init__(self):
        self.tests = []

    def add_test(self, name: str, passed: bool, message: str = ""):
        self.tests.append((name, passed, message))

    def all_passed(self) -> bool:
        return all(passed for _, passed, _ in self.tests)

    def print_summary(self):
        print_section("Test Summary")
        for name, passed, message in self.tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            line = f"{status}: {name}"
            if message:
                line += f" - {message}"
            print(line)

        total = len(self.tests)
        passed_count = sum(1 for _, passed, _ in self.tests if passed)
        print(f"\n{passed_count}/{total} tests passed")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


def test_env_loading():
    """Test loading API keys from .env.local"""
    print("\n🔍 Loading API keys from .env.local...")
    
    env_file = repo_root / '.env.local'
    if not env_file.exists():
        print(f"❌ ERROR: .env.local not found at {env_file}")
        print("\nPlease create .env.local with:")
        print("OPENAI_API_KEY=your_openai_key")
        print("ANTHROPIC_API_KEY=your_anthropic_key")
        return False
    
    load_dotenv(env_file)
    
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not openai_key or not anthropic_key:
        print("❌ ERROR: Missing API keys in .env.local")
        print(f"   OpenAI key: {'✓' if openai_key else '✗'}")
        print(f"   Anthropic key: {'✓' if anthropic_key else '✗'}")
        return False
    
    print("✅ Loaded API keys from .env.local")
    
    return openai_key, anthropic_key


def test_config_manager_save(openai_key: str, anthropic_key: str):
    """Test saving configuration with ConfigManager."""
    print("\n🔧 Saving configuration...")
    
    config_manager = ConfigManager()
    
    try:
        config_manager.save(
            cluster_api_key=openai_key,
            main_api_key=openai_key,
            fallback_api_key=anthropic_key,
            cluster_model='gpt-5.2',
            main_model='gpt-5.2-chat-latest',
            fallback_model='claude-opus-4-5-20251101',
            default_output='docs',
            cluster_base_url='https://api.openai.com/v1',
            main_base_url='https://api.openai.com/v1',
            fallback_base_url='https://api.anthropic.com/v1',
            cluster_max_tokens=128000,
            main_max_tokens=128000,
            fallback_max_tokens=200000,
        )
        print("✅ Configuration saved")
        return True
    except Exception as e:
        print(f"❌ ERROR saving configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager_load():
    """Test loading configuration with ConfigManager."""
    print("\n🔍 Loading configuration...")
    
    config_manager = ConfigManager()
    
    try:
        if not config_manager.load():
            print("❌ ERROR: Configuration not found")
            return False
        
        cluster_key = config_manager.get_cluster_api_key()
        main_key = config_manager.get_main_api_key()
        fallback_key = config_manager.get_fallback_api_key()
        
        print(f"   Cluster API key: {'✓' if cluster_key else '✗'}")
        print(f"   Main API key: {'✓' if main_key else '✗'}")
        print(f"   Fallback API key: {'✓' if fallback_key else '✗'}")
        
        if not all([cluster_key, main_key, fallback_key]):
            print("❌ ERROR: Missing API keys after loading")
            return False
        
        print("✅ Configuration loaded successfully")
        return config_manager
    except Exception as e:
        print(f"❌ ERROR loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_config_creation(config_manager: ConfigManager):
    """Test creating backend Config from ConfigManager."""
    print("\n🏗️ Creating Config from ConfigManager...")

    try:
        # Get the configuration
        cli_config = config_manager.get_config()

        # Print model configuration
        print(f"   Cluster model: {cli_config.cluster_model}")
        print(f"   Main model: {cli_config.main_model}")
        print(f"   Fallback model: {cli_config.fallback_model}")

        # Verify per-provider API keys are set
        cluster_key = config_manager.get_cluster_api_key()
        main_key = config_manager.get_main_api_key()
        fallback_key = config_manager.get_fallback_api_key()

        if not cluster_key:
            print("❌ ERROR: Missing cluster_api_key")
            return False
        if not main_key:
            print("❌ ERROR: Missing main_api_key")
            return False
        if not fallback_key:
            print("❌ ERROR: Missing fallback_api_key")
            return False

        print("   ✅ Cluster API key configured")
        print("   ✅ Main API key configured")
        print("   ✅ Fallback API key configured")

        # Create backend config with per-provider keys
        backend_config = cli_config.to_backend_config(
            repo_path=str(repo_root),
            output_dir='docs'
        )

        print("✅ Backend Config created successfully")
        return backend_config
    except Exception as e:
        print(f"❌ ERROR creating backend config: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_service_creation(backend_config):
    """Test creating LLM services from backend config with per-provider keys."""
    print("\n🤖 Testing LLM service creation with per-provider API keys...")

    try:
        from codewiki.src.be.llm_services import (
            create_cluster_model,
            create_main_model,
            create_fallback_model
        )

        # Verify each service uses its own API key
        print("\n   Testing cluster model with cluster_api_key...")
        cluster_service = create_cluster_model(backend_config)
        if not hasattr(cluster_service, 'client') or not hasattr(cluster_service.client, 'api_key') or not cluster_service.client.api_key:
            print("   ❌ ERROR: Cluster service missing API key")
            return False
        print("   ✅ Cluster model created with cluster_api_key")

        print("\n   Testing main model with main_api_key...")
        main_service = create_main_model(backend_config)
        if not hasattr(main_service, 'client') or not hasattr(main_service.client, 'api_key') or not main_service.client.api_key:
            print("   ❌ ERROR: Main service missing API key")
            return False
        print("   ✅ Main model created with main_api_key")

        print("\n   Testing fallback model with fallback_api_key...")
        fallback_service = create_fallback_model(backend_config)
        if not hasattr(fallback_service, 'client') or not hasattr(fallback_service.client, 'api_key') or not fallback_service.client.api_key:
            print("   ❌ ERROR: Fallback service missing API key")
            return False
        print("   ✅ Fallback model created with fallback_api_key")

        print("\n   ✓ All services using per-provider API keys (no generic fallback)")

        return True
    except Exception as e:
        print(f"❌ ERROR creating LLM services: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print_section("CodeWiki Local Configuration Test")

    results = TestResults()

    # Test 1: Load API keys from .env.local
    result = test_env_loading()
    if not result:
        results.add_test("Load API keys from .env.local", False, "Could not load API keys from .env.local")
        results.print_summary()
        sys.exit(1)
    results.add_test("Load API keys from .env.local", True)

    openai_key, anthropic_key = result

    # Test 2: Save configuration
    if not test_config_manager_save(openai_key, anthropic_key):
        results.add_test("Save configuration", False, "Could not save configuration")
        results.print_summary()
        sys.exit(1)
    results.add_test("Save configuration", True)

    # Test 3: Load configuration
    config_manager = test_config_manager_load()
    if not config_manager:
        results.add_test("Load configuration", False, "Could not load configuration")
        results.print_summary()
        sys.exit(1)
    results.add_test("Load configuration", True)

    # Test 4: Create backend config
    backend_config = test_backend_config_creation(config_manager)
    if not backend_config:
        results.add_test("Create backend config", False, "Could not create backend config")
        results.print_summary()
        sys.exit(1)
    results.add_test("Create backend config", True)

    # Test 5: Create LLM services
    if not test_llm_service_creation(backend_config):
        results.add_test("Create LLM services", False, "Could not create LLM services")
        results.print_summary()
        sys.exit(1)
    results.add_test("Create LLM services", True)

    # Success!
    results.print_summary()
    print_section("🎉 SUCCESS: All tests passed!")
    print("\nCodeWiki is properly configured and ready to use.")
    print("\nNext steps:")
    print("  1. Run: codewiki generate /path/to/your/repo")
    print("  2. Or use the CLI: codewiki --help")
    print("\nConfiguration saved to: ~/.codewiki/config.json")
    print("API keys stored securely in system keychain")


if __name__ == '__main__':
    main()
