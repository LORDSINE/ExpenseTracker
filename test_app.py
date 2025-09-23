#!/usr/bin/env python3
"""
Test script to verify the app works without Flask-WTF/WTForms
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_app_imports():
    """Test that the app imports without Flask-WTF dependencies"""
    try:
        from app import app, db, User, Transaction
        print("✓ App imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Other error: {e}")
        return False

def test_app_creation():
    """Test that Flask app can be created"""
    try:
        from app import app
        with app.app_context():
            print("✓ Flask app context works")
            return True
    except Exception as e:
        print(f"✗ App context error: {e}")
        return False

def test_routes_exist():
    """Test that required routes are defined"""
    try:
        from app import app
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(str(rule))
        
        required_routes = ['/health', '/login', '/register', '/']
        missing_routes = []
        
        for req_route in required_routes:
            if not any(req_route in route for route in routes):
                missing_routes.append(req_route)
        
        if missing_routes:
            print(f"✗ Missing routes: {missing_routes}")
            return False
        else:
            print("✓ All required routes exist")
            print(f"✓ Total routes found: {len(routes)}")
            return True
            
    except Exception as e:
        print(f"✗ Route test error: {e}")
        return False

def main():
    print("Testing Flask app without Flask-WTF/WTForms...")
    print("=" * 50)
    
    tests = [
        test_app_imports,
        test_app_creation,
        test_routes_exist
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! App is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)