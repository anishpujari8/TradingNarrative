"""Backend API tests for audio narration bug fixes."""
import requests
import sys
import base64

BASE_URL = "https://insight-hub-484.preview.emergentagent.com/api"

class AudioNarrationTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log(self, test_name, passed, message=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {test_name}")
            if message:
                print(f"   {message}")
        else:
            print(f"❌ FAIL: {test_name}")
            print(f"   {message}")
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })

    def test_admin_login(self):
        """Test admin authentication"""
        print("\n🔐 Testing Admin Login...")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": "admin@tradingnarrative.com", "password": "Admin@2025"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.log("Admin Login", True, f"Token received: {self.token[:20]}...")
                return True
            else:
                self.log("Admin Login", False, f"Status {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            self.log("Admin Login", False, f"Exception: {str(e)}")
            return False

    def test_working_narration_shipping(self):
        """Test working narration: shipping-industry article (~4.3MB)"""
        print("\n🎵 Testing Working Narration: Shipping Industry...")
        slug = "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a"
        try:
            response = requests.get(
                f"{BASE_URL}/posts/{slug}/audio?voice=male",
                timeout=60
            )
            if response.status_code == 200:
                size_mb = len(response.content) / (1024 * 1024)
                cache_header = response.headers.get("X-Audio-Cache", "miss")
                if size_mb >= 3.0 and size_mb <= 6.0:
                    self.log(
                        "Shipping Industry Narration",
                        True,
                        f"Size: {size_mb:.2f}MB, Cache: {cache_header}"
                    )
                else:
                    self.log(
                        "Shipping Industry Narration",
                        False,
                        f"Unexpected size: {size_mb:.2f}MB (expected ~4.3MB)"
                    )
            else:
                self.log(
                    "Shipping Industry Narration",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Shipping Industry Narration", False, f"Exception: {str(e)}")

    def test_working_narration_freight(self):
        """Test working narration: freight-management article (~5.3MB)"""
        print("\n🎵 Testing Working Narration: Freight Management...")
        slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
        try:
            response = requests.get(
                f"{BASE_URL}/posts/{slug}/audio?voice=male",
                timeout=60
            )
            if response.status_code == 200:
                size_mb = len(response.content) / (1024 * 1024)
                cache_header = response.headers.get("X-Audio-Cache", "miss")
                if size_mb >= 4.0 and size_mb <= 7.0:
                    self.log(
                        "Freight Management Narration",
                        True,
                        f"Size: {size_mb:.2f}MB, Cache: {cache_header}"
                    )
                else:
                    self.log(
                        "Freight Management Narration",
                        False,
                        f"Unexpected size: {size_mb:.2f}MB (expected ~5.3MB)"
                    )
            else:
                self.log(
                    "Freight Management Narration",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Freight Management Narration", False, f"Exception: {str(e)}")

    def test_170km_honest_error(self):
        """Test 170km slug returns honest 503 error (not corrupt audio)"""
        print("\n⚠️  Testing 170km Honest Error Response...")
        slug = "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        try:
            response = requests.get(
                f"{BASE_URL}/posts/{slug}/audio?voice=male",
                timeout=30
            )
            if response.status_code == 503:
                try:
                    data = response.json()
                    detail = data.get("detail", "")
                    if "audio credits are being refilled" in detail.lower() or "credits refilling" in detail.lower():
                        self.log(
                            "170km Honest Error",
                            True,
                            f"Correct 503 response: {detail}"
                        )
                    else:
                        self.log(
                            "170km Honest Error",
                            False,
                            f"503 but wrong message: {detail}"
                        )
                except:
                    self.log(
                        "170km Honest Error",
                        False,
                        f"503 but not JSON: {response.text[:200]}"
                    )
            elif response.status_code == 200:
                size_mb = len(response.content) / (1024 * 1024)
                if size_mb < 0.1:
                    self.log(
                        "170km Honest Error",
                        False,
                        f"CORRUPT AUDIO SERVED: 200 status with tiny {size_mb:.2f}MB payload"
                    )
                else:
                    self.log(
                        "170km Honest Error",
                        True,
                        f"Valid audio served: {size_mb:.2f}MB (credits may have been refilled)"
                    )
            else:
                self.log(
                    "170km Honest Error",
                    False,
                    f"Unexpected status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("170km Honest Error", False, f"Exception: {str(e)}")

    def test_import_endpoint_validation(self):
        """Test import endpoint validation (SAFE: only nonexistent slug)"""
        print("\n🔒 Testing Import Endpoint Validation...")
        if not self.token:
            self.log("Import Endpoint Validation", False, "No admin token available")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test 1: Nonexistent slug (should return 404 before any write)
        print("   Testing with nonexistent slug...")
        try:
            response = requests.post(
                f"{BASE_URL}/admin/audio-cache/import",
                json={
                    "post_slug": "nonexistent-slug-xyz",
                    "voice": "male",
                    "scope": "full",
                    "audio_b64": base64.b64encode(b"hello").decode()
                },
                headers=headers,
                timeout=10
            )
            if response.status_code == 404 and "not published" in response.text.lower():
                self.log(
                    "Import: Nonexistent Slug",
                    True,
                    "Correctly returns 404 for nonexistent slug"
                )
            else:
                self.log(
                    "Import: Nonexistent Slug",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Import: Nonexistent Slug", False, f"Exception: {str(e)}")

        # Test 2: Invalid voice (should return 400)
        print("   Testing with invalid voice...")
        try:
            response = requests.post(
                f"{BASE_URL}/admin/audio-cache/import",
                json={
                    "post_slug": "nonexistent-slug-xyz",
                    "voice": "robot",
                    "scope": "full",
                    "audio_b64": base64.b64encode(b"hello").decode()
                },
                headers=headers,
                timeout=10
            )
            if response.status_code == 400 and "invalid voice" in response.text.lower():
                self.log(
                    "Import: Invalid Voice",
                    True,
                    "Correctly returns 400 for invalid voice"
                )
            else:
                self.log(
                    "Import: Invalid Voice",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Import: Invalid Voice", False, f"Exception: {str(e)}")

        # Test 3: No auth (should return 401/403)
        print("   Testing without authentication...")
        try:
            response = requests.post(
                f"{BASE_URL}/admin/audio-cache/import",
                json={
                    "post_slug": "nonexistent-slug-xyz",
                    "voice": "male",
                    "scope": "full",
                    "audio_b64": base64.b64encode(b"hello").decode()
                },
                timeout=10
            )
            if response.status_code in [401, 403]:
                self.log(
                    "Import: No Auth",
                    True,
                    f"Correctly returns {response.status_code} without auth"
                )
            else:
                self.log(
                    "Import: No Auth",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Import: No Auth", False, f"Exception: {str(e)}")

    def test_admin_narrations_endpoint(self):
        """Test admin narrations status endpoint"""
        print("\n📊 Testing Admin Narrations Endpoint...")
        if not self.token:
            self.log("Admin Narrations Endpoint", False, "No admin token available")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(
                f"{BASE_URL}/admin/narrations",
                headers=headers,
                timeout=20
            )
            if response.status_code == 200:
                data = response.json()
                cached_count = data.get("cached_count", 0)
                total = data.get("total", 0)
                essays = data.get("essays", [])
                
                # Check that shipping and freight are cached
                shipping_cached = any(
                    e["slug"] == "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a" 
                    and e.get("cached")
                    for e in essays
                )
                freight_cached = any(
                    e["slug"] == "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
                    and e.get("cached")
                    for e in essays
                )
                
                # Check that 170km is NOT cached (purged)
                km170_not_cached = all(
                    e["slug"] != "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
                    or not e.get("cached")
                    for e in essays
                )
                
                if shipping_cached and freight_cached and km170_not_cached:
                    self.log(
                        "Admin Narrations Endpoint",
                        True,
                        f"Cached: {cached_count}/{total}, shipping+freight cached, 170km purged"
                    )
                else:
                    self.log(
                        "Admin Narrations Endpoint",
                        False,
                        f"Cache state incorrect: shipping={shipping_cached}, freight={freight_cached}, 170km_purged={km170_not_cached}"
                    )
            else:
                self.log(
                    "Admin Narrations Endpoint",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Admin Narrations Endpoint", False, f"Exception: {str(e)}")

    def test_sync_narrations_auth(self):
        """Test sync narrations endpoint requires auth"""
        print("\n🔄 Testing Sync Narrations Auth...")
        try:
            response = requests.post(
                f"{BASE_URL}/admin/sync/narrations",
                json={"password": "wrong"},
                timeout=10
            )
            if response.status_code in [401, 403]:
                self.log(
                    "Sync Narrations Auth",
                    True,
                    f"Correctly returns {response.status_code} with wrong password"
                )
            else:
                self.log(
                    "Sync Narrations Auth",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Sync Narrations Auth", False, f"Exception: {str(e)}")

    def test_posts_list(self):
        """Test posts list endpoint (regression)"""
        print("\n📝 Testing Posts List Endpoint...")
        try:
            response = requests.get(
                f"{BASE_URL}/posts?limit=10",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])
                if len(posts) > 0:
                    self.log(
                        "Posts List Endpoint",
                        True,
                        f"Retrieved {len(posts)} posts"
                    )
                else:
                    self.log(
                        "Posts List Endpoint",
                        False,
                        "No posts returned"
                    )
            else:
                self.log(
                    "Posts List Endpoint",
                    False,
                    f"Status {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            self.log("Posts List Endpoint", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("🧪 AUDIO NARRATION BUG FIX TESTS")
        print("=" * 80)
        
        # Login first
        if not self.test_admin_login():
            print("\n❌ Cannot proceed without admin authentication")
            return False
        
        # Run all tests
        self.test_working_narration_shipping()
        self.test_working_narration_freight()
        self.test_170km_honest_error()
        self.test_import_endpoint_validation()
        self.test_admin_narrations_endpoint()
        self.test_sync_narrations_auth()
        self.test_posts_list()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} TESTS FAILED")
            return False

def main():
    tester = AudioNarrationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
