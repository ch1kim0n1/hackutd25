"""
APEX Setup Test Script
Tests that all Phase 1 components are working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Test results
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def test_imports():
    """Test 1: Can we import all required packages?"""
    test_name = "Package Imports"
    try:
        import fastapi
        import uvicorn
        import redis
        import pandas
        import numpy
        import yfinance
        
        try:
            import cupy
            results["passed"].append(f"{test_name} (with GPU support)")
        except ImportError:
            results["warnings"].append(f"{test_name}: CuPy not installed (GPU disabled)")
            results["passed"].append(f"{test_name} (CPU only)")
            
    except ImportError as e:
        results["failed"].append(f"{test_name}: {e}")


def test_redis():
    """Test 2: Can we connect to Redis?"""
    test_name = "Redis Connection"
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
        r.ping()
        results["passed"].append(test_name)
    except redis.ConnectionError:
        results["warnings"].append(f"{test_name}: Redis not running (orchestrator state will be memory-only)")
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_api_keys():
    """Test 3: Are API keys configured?"""
    test_name = "API Keys"
    import os
    
    keys_found = []
    keys_missing = []
    
    # Check for OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        keys_found.append("OpenRouter")
    else:
        keys_missing.append("OpenRouter (for AI agents)")
    
    # Check for Alpaca
    if os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY"):
        keys_found.append("Alpaca")
    else:
        keys_missing.append("Alpaca (for trading)")
    
    if keys_found:
        results["passed"].append(f"{test_name}: {', '.join(keys_found)}")
    
    if keys_missing:
        results["warnings"].append(f"{test_name}: Missing {', '.join(keys_missing)}")


def test_historical_data():
    """Test 4: Can we load historical data?"""
    test_name = "Historical Data Loader"
    try:
        from services.historical_data import HistoricalDataLoader
        
        loader = HistoricalDataLoader()
        
        # Try to load 2008 crisis (from cache or download)
        data = loader.load_scenario("2008_crisis")
        
        if "SPY" in data["symbols"]:
            num_days = len(data["symbols"]["SPY"]["dates"])
            results["passed"].append(f"{test_name}: 2008 crisis loaded ({num_days} days)")
        else:
            results["warnings"].append(f"{test_name}: Data downloaded but SPY missing")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_server_config():
    """Test 5: Can we create FastAPI server?"""
    test_name = "FastAPI Server"
    try:
        from server import app
        
        if app:
            results["passed"].append(f"{test_name}: App created successfully")
        else:
            results["failed"].append(f"{test_name}: App is None")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_orchestrator():
    """Test 6: Can we create orchestrator?"""
    test_name = "Orchestrator"
    try:
        # First check if Enum is imported
        from orchestrator import OrchestratorState, Orchestrator
        
        # Create orchestrator (it will fail to connect to Redis but that's ok for test)
        try:
            orch = Orchestrator(redis_url="redis://localhost:6379")
            results["passed"].append(f"{test_name}: Created successfully")
        except Exception as e:
            # If it fails due to Redis, that's a warning not a failure
            if "redis" in str(e).lower() or "connection" in str(e).lower():
                results["warnings"].append(f"{test_name}: Created but Redis unavailable")
            else:
                results["failed"].append(f"{test_name}: {e}")
                
    except ImportError as e:
        results["failed"].append(f"{test_name}: Import error - {e}")
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


async def test_server_start():
    """Test 7: Can we start the server?"""
    test_name = "Server Startup"
    try:
        import uvicorn
        from server import app
        
        # Just verify we can access the app
        # Don't actually start it (would block)
        if hasattr(app, 'routes'):
            num_routes = len(app.routes)
            results["passed"].append(f"{test_name}: Ready ({num_routes} routes)")
        else:
            results["warnings"].append(f"{test_name}: App has no routes")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def print_results():
    """Print test results in a nice format."""
    print("\n" + "="*70)
    print("🔧 APEX PHASE 1 SETUP TEST RESULTS")
    print("="*70)
    
    if results["passed"]:
        print(f"\n✅ PASSED ({len(results['passed'])} tests)")
        for test in results["passed"]:
            print(f"   ✓ {test}")
    
    if results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])} items)")
        for warning in results["warnings"]:
            print(f"   ! {warning}")
    
    if results["failed"]:
        print(f"\n❌ FAILED ({len(results['failed'])} tests)")
        for failure in results["failed"]:
            print(f"   ✗ {failure}")
    
    print("\n" + "="*70)
    
    # Overall status
    total_tests = len(results["passed"]) + len(results["failed"])
    if results["failed"]:
        print(f"❌ PHASE 1 INCOMPLETE: {len(results['failed'])}/{total_tests} tests failed")
        print("\nNext steps:")
        if any("redis" in f.lower() for f in results["warnings"] + results["failed"]):
            print("  1. Install and start Redis: docker run -d -p 6379:6379 redis")
        if any("api" in f.lower() for f in results["warnings"]):
            print("  2. Set API keys in environment variables")
        print("\n")
        return 1
    else:
        print(f"✅ PHASE 1 READY: All {total_tests} critical tests passed")
        if results["warnings"]:
            print("\n⚠️  Some warnings present but system can run")
        print("\nYou can now proceed to Phase 2!")
        print("\n")
        return 0


def main():
    """Run all tests."""
    print("\n🚀 Starting APEX Phase 1 Setup Tests...\n")
    
    # Run synchronous tests
    test_imports()
    test_redis()
    test_api_keys()
    test_historical_data()
    test_server_config()
    test_orchestrator()
    
    # Run async tests
    asyncio.run(test_server_start())
    
    # Print results
    exit_code = print_results()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
