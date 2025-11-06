"""
Quick test script to validate Research Orchestrator setup
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from research_orchestrator import ResearchOrchestrator


def check_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...")

    required_packages = {
        "claude_agent_sdk": "Claude Agent SDK",
        "streamlit": "Streamlit",
        "requests": "Requests"
    }

    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - Not installed")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed\n")
    return True


def check_api_keys():
    """Check if API keys are configured"""
    print("🔑 Checking API keys...")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    serper_key = os.getenv("SERPERDEV_API_KEY")

    if not anthropic_key:
        print("  ❌ ANTHROPIC_API_KEY not set")
        print("     Get from: https://console.anthropic.com")
    else:
        print(f"  ✅ ANTHROPIC_API_KEY: {anthropic_key[:8]}...")

    if not serper_key:
        print("  ❌ SERPERDEV_API_KEY not set")
        print("     Get from: https://serper.dev")
    else:
        print(f"  ✅ SERPERDEV_API_KEY: {serper_key[:8]}...")

    if not anthropic_key or not serper_key:
        print("\n❌ Missing API keys")
        print("Set them with:")
        print("  export ANTHROPIC_API_KEY='your_key'")
        print("  export SERPERDEV_API_KEY='your_key'")
        return False

    print("✅ All API keys configured\n")
    return True


async def run_quick_test():
    """Run a quick test of the research orchestrator"""
    print("🧪 Running quick test...")
    print("-" * 60)

    serper_key = os.getenv("SERPERDEV_API_KEY")

    # Create orchestrator with minimal results for quick test
    orchestrator = ResearchOrchestrator(serper_key, num_results=3)

    # Simple test query
    test_query = "Python programming best practices"

    print(f"📝 Test Query: '{test_query}'")
    print(f"📊 Results per query: 3 (quick test mode)")
    print("-" * 60)

    try:
        result = await orchestrator.research_with_orchestrator(test_query)

        print("\n" + "=" * 60)
        print("✅ TEST PASSED - Research Orchestrator Working!")
        print("=" * 60)
        print(f"\n📁 Session Directory: {result['session_dir']}")
        print(f"📊 Total Articles: {sum([r.get('num_articles', 0) for r in result['results']])}")
        print(f"📝 Report Length: {len(result['report'])} characters")

        print("\n" + "-" * 60)
        print("📄 Report Preview (first 500 chars):")
        print("-" * 60)
        print(result['report'][:500] + "...")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check API keys are valid")
        print("2. Check internet connection")
        print("3. Check Serper.dev API quota")
        return False


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("🔬 RESEARCH ORCHESTRATOR - SETUP VALIDATION")
    print("=" * 60 + "\n")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check API keys
    if not check_api_keys():
        sys.exit(1)

    # Run test
    print("🚀 Starting Research Orchestrator test...")
    print("   This will:")
    print("   1. Refine your query into 3 search variants")
    print("   2. Execute 3 parallel searches (3 results each)")
    print("   3. Scrape content from 9 total URLs")
    print("   4. Generate a research report")
    print()

    input("Press Enter to continue (or Ctrl+C to cancel)...")
    print()

    success = asyncio.run(run_quick_test())

    if success:
        print("\n" + "=" * 60)
        print("✨ All tests passed! System is ready to use.")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run the Streamlit UI: streamlit run app.py")
        print("2. Or use the CLI: python research_orchestrator.py")
        print()
    else:
        print("\n" + "=" * 60)
        print("⚠️  Setup validation failed")
        print("=" * 60)
        print("Please fix the issues above and try again.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
