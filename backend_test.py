"""Backend API tests for narration sync feature and bug verification."""
import requests
import sys
import base64
from datetime import datetime

BASE_URL = "https://insight-hub-484.preview.emergentagent.com"
ADMIN_EMAIL = "admin@tradingnarrative.com"
ADMIN_PASSWORD = "Admin@2025"

class NarrationSyncTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log(self, test_name, passed, detail=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {test_name}")
        else:
            print(f"❌ FAIL: {test_name}")
            if detail:
                print(f"   Detail: {detail}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "detail": detail
        })

    def login(self):
        """Login as admin and get token"""
        print("\n🔐 Logging in as admin...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                print(f"✅ Login successful, token obtained")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False

    def get_headers(self, auth=True):
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ==================== BUG VERIFICATION ====================
    
    def test_cached_audio_endpoints(self):
        """Test GET /api/posts/{slug}/audio for 3 cached essays"""
        print("\n📻 Testing cached audio endpoints...")
        
        cached_slugs = [
            "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a",
            "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
            "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        ]
        
        for idx, slug in enumerate(cached_slugs):
            try:
                response = requests.get(
                    f"{BASE_URL}/api/posts/{slug}/audio?voice=male",
                    timeout=10
                )
                
                # Check status code
                status_ok = response.status_code == 200
                
                # Check content type
                content_type = response.headers.get("Content-Type", "")
                content_type_ok = "audio" in content_type.lower()
                
                # Check cache header
                cache_header = response.headers.get("X-Audio-Cache", "")
                cache_ok = cache_header == "hit"
                
                # Check size (should be ~2MB, let's check > 0.5MB)
                # Note: Skip size check for last slug as it will be modified by import test
                size_mb = len(response.content) / (1024 * 1024)
                if idx < 2:  # Only check size for first 2 slugs
                    size_ok = size_mb > 0.5  # At least 0.5MB
                else:
                    size_ok = True  # Will be modified by import test, so skip size check
                
                all_ok = status_ok and content_type_ok and cache_ok and size_ok
                
                detail = f"Status: {response.status_code}, Type: {content_type}, Cache: {cache_header}, Size: {size_mb:.2f}MB"
                self.log(f"Audio endpoint: {slug[:50]}...", all_ok, detail)
                
            except Exception as e:
                self.log(f"Audio endpoint: {slug[:50]}...", False, str(e))

    # ==================== NEW FEATURE: IMPORT ENDPOINT ====================
    
    def test_import_invalid_voice(self):
        """Test POST /api/admin/audio-cache/import with invalid voice"""
        print("\n🔧 Testing audio cache import - invalid voice...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/audio-cache/import",
                headers=self.get_headers(),
                json={
                    "post_slug": "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum",
                    "voice": "invalid_voice",
                    "scope": "full",
                    "audio_b64": "dGVzdA==",  # base64 "test"
                    "chars": 100
                },
                timeout=10
            )
            
            passed = response.status_code == 400 and "Invalid voice or scope" in response.text
            self.log("Import with invalid voice returns 400", passed, 
                    f"Status: {response.status_code}, Response: {response.text[:100]}")
            
        except Exception as e:
            self.log("Import with invalid voice returns 400", False, str(e))

    def test_import_unknown_slug(self):
        """Test POST /api/admin/audio-cache/import with unknown slug"""
        print("\n🔧 Testing audio cache import - unknown slug...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/audio-cache/import",
                headers=self.get_headers(),
                json={
                    "post_slug": "nonexistent-post-slug-12345",
                    "voice": "male",
                    "scope": "full",
                    "audio_b64": "dGVzdA==",
                    "chars": 100
                },
                timeout=10
            )
            
            passed = response.status_code == 404
            self.log("Import with unknown slug returns 404", passed,
                    f"Status: {response.status_code}, Response: {response.text[:100]}")
            
        except Exception as e:
            self.log("Import with unknown slug returns 404", False, str(e))

    def test_import_valid_reimport(self):
        """Test POST /api/admin/audio-cache/import with valid re-import"""
        print("\n🔧 Testing audio cache import - valid re-import...")
        try:
            # Create a small valid audio payload (just some bytes)
            audio_bytes = b"RIFF" + b"\x00" * 1000  # Minimal audio-like data
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            response = requests.post(
                f"{BASE_URL}/api/admin/audio-cache/import",
                headers=self.get_headers(),
                json={
                    "post_slug": "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum",
                    "voice": "male",
                    "scope": "full",
                    "audio_b64": audio_b64,
                    "chars": 5000
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                passed = data.get("ok") == True and "bytes" in data
                detail = f"Response: {data}"
            else:
                passed = False
                detail = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log("Import valid re-import returns ok:true with bytes", passed, detail)
            
            # Verify the audio endpoint still serves cache hit
            if passed:
                audio_response = requests.get(
                    f"{BASE_URL}/api/posts/170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum/audio?voice=male",
                    timeout=10
                )
                cache_header = audio_response.headers.get("X-Audio-Cache", "")
                cache_ok = cache_header == "hit"
                self.log("After re-import, audio endpoint still returns cache hit", cache_ok,
                        f"Cache header: {cache_header}")
            
        except Exception as e:
            self.log("Import valid re-import returns ok:true with bytes", False, str(e))

    def test_import_without_auth(self):
        """Test POST /api/admin/audio-cache/import without authentication"""
        print("\n🔧 Testing audio cache import - no auth...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/audio-cache/import",
                headers={"Content-Type": "application/json"},  # No auth header
                json={
                    "post_slug": "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum",
                    "voice": "male",
                    "scope": "full",
                    "audio_b64": "dGVzdA==",
                    "chars": 100
                },
                timeout=10
            )
            
            passed = response.status_code in [401, 403]
            self.log("Import without auth returns 401/403", passed,
                    f"Status: {response.status_code}")
            
        except Exception as e:
            self.log("Import without auth returns 401/403", False, str(e))

    # ==================== NEW FEATURE: SYNC NARRATIONS ====================
    
    def test_sync_narrations_wrong_password(self):
        """Test POST /api/admin/sync/narrations with wrong password"""
        print("\n🔄 Testing sync narrations - wrong password...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/sync/narrations",
                headers=self.get_headers(),
                json={"password": "wrongpass123"},
                timeout=30
            )
            
            passed = (response.status_code == 401 and 
                     "Production sign-in failed" in response.text)
            self.log("Sync narrations with wrong password returns 401", passed,
                    f"Status: {response.status_code}, Response: {response.text[:150]}")
            
        except Exception as e:
            self.log("Sync narrations with wrong password returns 401", False, str(e))

    # ==================== REGRESSION TESTS ====================
    
    def test_admin_narrations_endpoint(self):
        """Test GET /api/admin/narrations (regression)"""
        print("\n🔍 Testing admin narrations endpoint (regression)...")
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/narrations",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                has_essays = "essays" in data
                has_cached_count = "cached_count" in data
                has_credits = "credits" in data
                
                # Check if essays have expected fields
                essays_ok = True
                if has_essays and len(data["essays"]) > 0:
                    first_essay = data["essays"][0]
                    essays_ok = all(k in first_essay for k in ["slug", "title", "cached"])
                
                passed = has_essays and has_cached_count and essays_ok
                
                # Handle credits safely
                credits_info = "N/A"
                if data.get("credits") and isinstance(data["credits"], dict):
                    credits_info = data["credits"].get("remaining", "N/A")
                
                detail = f"Essays: {len(data.get('essays', []))}, Cached: {data.get('cached_count')}, Credits: {credits_info}"
            else:
                passed = False
                detail = f"Status: {response.status_code}"
            
            self.log("Admin narrations endpoint returns essays list", passed, detail)
            
        except Exception as e:
            self.log("Admin narrations endpoint returns essays list", False, str(e))

    def test_sync_diff_endpoint(self):
        """Test GET /api/admin/sync/diff (regression)"""
        print("\n🔍 Testing sync diff endpoint (regression)...")
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/sync/diff",
                headers=self.get_headers(),
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                has_production_url = "production_url" in data
                has_missing = "missing" in data
                passed = has_production_url and has_missing
                detail = f"Production URL: {data.get('production_url', 'N/A')}, Missing posts: {len(data.get('missing', []))}"
            else:
                passed = False
                detail = f"Status: {response.status_code}, Response: {response.text[:150]}"
            
            self.log("Sync diff endpoint works", passed, detail)
            
        except Exception as e:
            self.log("Sync diff endpoint works", False, str(e))

    def test_posts_endpoint(self):
        """Test GET /api/posts (regression)"""
        print("\n🔍 Testing posts endpoint (regression)...")
        try:
            response = requests.get(
                f"{BASE_URL}/api/posts?limit=5",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                has_posts = "posts" in data
                posts_count = len(data.get("posts", []))
                passed = has_posts and posts_count > 0
                detail = f"Posts returned: {posts_count}"
            else:
                passed = False
                detail = f"Status: {response.status_code}"
            
            self.log("Posts endpoint works", passed, detail)
            
        except Exception as e:
            self.log("Posts endpoint works", False, str(e))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print(f"📊 TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("="*60)
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['test']}")
                    if r["detail"]:
                        print(f"    {r['detail']}")

def main():
    print("🚀 Starting Narration Sync Backend Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    
    tester = NarrationSyncTester()
    
    # Login first
    if not tester.login():
        print("\n❌ Cannot proceed without authentication")
        return 1
    
    # Run all tests
    tester.test_cached_audio_endpoints()
    tester.test_import_invalid_voice()
    tester.test_import_unknown_slug()
    tester.test_import_valid_reimport()
    tester.test_import_without_auth()
    tester.test_sync_narrations_wrong_password()
    tester.test_admin_narrations_endpoint()
    tester.test_sync_diff_endpoint()
    tester.test_posts_endpoint()
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
