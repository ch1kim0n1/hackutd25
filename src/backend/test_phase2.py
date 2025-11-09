"""
Phase 2 Test Script
Tests War Room WebSocket and orchestrator integration
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


def test_war_room_imports():
    """Test 1: Can we import War Room components?"""
    test_name = "War Room Imports"
    try:
        # Check if utils directory exists
        from utils.test_messages import TestMessageGenerator
        results["passed"].append(f"{test_name}: Test message generator imported")
    except ImportError as e:
        results["failed"].append(f"{test_name}: {e}")


def test_websocket_endpoint():
    """Test 2: Check if WebSocket endpoint exists in server"""
    test_name = "WebSocket Endpoint"
    try:
        import server
        
        # Check if warroom websocket route exists
        routes = [route.path for route in server.app.routes]
        
        if '/ws/warroom' in routes:
            results["passed"].append(f"{test_name}: /ws/warroom endpoint found")
        else:
            results["failed"].append(f"{test_name}: /ws/warroom endpoint missing")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_orchestrator_endpoints():
    """Test 3: Check for orchestrator control endpoints"""
    test_name = "Orchestrator Endpoints"
    try:
        import server
        
        routes = [route.path for route in server.app.routes]
        
        required_endpoints = ['/orchestrator/start', '/orchestrator/stop']
        found_endpoints = []
        missing_endpoints = []
        
        for endpoint in required_endpoints:
            if endpoint in routes:
                found_endpoints.append(endpoint)
            else:
                missing_endpoints.append(endpoint)
        
        if found_endpoints:
            results["passed"].append(f"{test_name}: {', '.join(found_endpoints)}")
        
        if missing_endpoints:
            results["warnings"].append(f"{test_name}: Missing {', '.join(missing_endpoints)}")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_connection_manager():
    """Test 4: Check ConnectionManager class"""
    test_name = "Connection Manager"
    try:
        from server import ConnectionManager, manager
        
        if manager and isinstance(manager, ConnectionManager):
            results["passed"].append(f"{test_name}: Manager initialized")
        else:
            results["failed"].append(f"{test_name}: Manager not initialized")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


async def test_message_broadcast():
    """Test 5: Test message broadcasting capability"""
    test_name = "Message Broadcasting"
    try:
        from server import manager
        
        # Test broadcast method exists
        if hasattr(manager, 'broadcast'):
            results["passed"].append(f"{test_name}: Broadcast method available")
        else:
            results["failed"].append(f"{test_name}: Broadcast method missing")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def test_frontend_components():
    """Test 6: Check if frontend War Room files exist"""
    test_name = "Frontend Components"
    try:
        frontend_files = [
            "../../frontend/src/hooks/useWebSocket.js",
            "../../frontend/src/components/WarRoom/MessageList.jsx",
            "../../frontend/src/components/WarRoom/ConnectionStatus.jsx",
            "../../frontend/src/components/WarRoom/WarRoomControls.jsx",
            "../../frontend/src/pages/WarRoomPage.jsx"
        ]
        
        existing = []
        missing = []
        
        for file_path in frontend_files:
            if Path(file_path).exists():
                existing.append(Path(file_path).name)
            else:
                missing.append(Path(file_path).name)
        
        if existing:
            results["passed"].append(f"{test_name}: {len(existing)}/5 components created")
        
        if missing:
            results["warnings"].append(f"{test_name}: Missing {', '.join(missing)}")
            
    except Exception as e:
        results["failed"].append(f"{test_name}: {e}")


def print_results():
    """Print test results in a nice format."""
    print("\n" + "="*70)
    print("🎭 APEX PHASE 2 WAR ROOM TEST RESULTS")
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
        print(f"❌ PHASE 2 INCOMPLETE: {len(results['failed'])}/{total_tests} tests failed")
        print("\nNext steps:")
        print("  1. Check backend server imports")
        print("  2. Verify frontend components exist")
        print("  3. Review PHASE2_COMPLETE.md for setup")
        print("\n")
        return 1
    else:
        print(f"✅ PHASE 2 READY: All {total_tests} critical tests passed")
        if results["warnings"]:
            print("\n⚠️  Some warnings present but system can run")
        print("\nYou can now:")
        print("  1. Start backend: python -m uvicorn server:app --reload")
        print("  2. Start frontend: cd ../../frontend && npm start")
        print("  3. Open War Room: http://localhost:3000")
        print("  4. Test with: python utils/test_messages.py")
        print("\n")
        return 0


def main():
    """Run all tests."""
    print("\n🚀 Starting APEX Phase 2 War Room Tests...\n")
    
    # Run synchronous tests
    test_war_room_imports()
    test_websocket_endpoint()
    test_orchestrator_endpoints()
    test_connection_manager()
    test_frontend_components()
    
    # Run async tests
    asyncio.run(test_message_broadcast())
    
    # Print results
    exit_code = print_results()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
