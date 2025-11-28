"""
Simple test script to verify app functionality
"""

import sys

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import flask
        import yt_dlp
        import qrcode
        import PIL
        print("✓ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_app_structure():
    """Test that app.py has the required structure"""
    try:
        import app
        
        # Check required functions exist
        required_functions = [
            'generate_qr_code',
            'resolve_base_url',
            'get_format_selector',
            'progress_hook',
            'download_worker'
        ]
        
        for func_name in required_functions:
            if not hasattr(app, func_name):
                print(f"✗ Missing function: {func_name}")
                return False
        
        # Check Flask app exists
        if not hasattr(app, 'app'):
            print("✗ Flask app not found")
            return False
        
        print("✓ App structure is correct")
        return True
    except Exception as e:
        print(f"✗ App structure test failed: {e}")
        return False

def test_routes():
    """Test that required routes are registered"""
    try:
        import app
        
        required_routes = [
            '/',
            '/about',
            '/api/metadata',
            '/api/download',
            '/api/status/<job_id>',
            '/api/progress/<job_id>',
            '/download/<job_id>/<path:filename>'
        ]
        
        registered_routes = [str(rule) for rule in app.app.url_map.iter_rules()]
        
        for route in required_routes:
            # Simple check - just verify the route pattern exists
            route_base = route.split('<')[0].rstrip('/')
            if not any(route_base in r for r in registered_routes):
                print(f"✗ Missing route: {route}")
                return False
        
        print("✓ All required routes are registered (including /api/progress)")
        return True
    except Exception as e:
        print(f"✗ Route test failed: {e}")
        return False

def test_format_selector():
    """Test format selector function"""
    try:
        import app
        
        # Test MP3 format
        mp3_format = app.get_format_selector('mp3')
        if 'bestaudio' not in mp3_format:
            print("✗ MP3 format selector incorrect")
            return False
        
        # Test MP4 format (should be 360p)
        mp4_format = app.get_format_selector('mp4')
        if '360' not in mp4_format:
            print("✗ MP4 format selector not set to 360p")
            return False
        
        print("✓ Format selectors are correct (360p for video, best audio for MP3)")
        return True
    except Exception as e:
        print(f"✗ Format selector test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing YTDownloadX Simplified Version")
    print("=" * 50)
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("App Structure Test", test_app_structure),
        ("Routes Test", test_routes),
        ("Format Selector Test", test_format_selector)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("\n✓ All tests passed! App is ready to use.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
