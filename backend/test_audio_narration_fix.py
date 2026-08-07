"""
Test audio narration bug fix: ElevenLabs quota exhausted handling
- Uncached essays should return 503 with specific message about credits
- Cached essays should still return 200 with audio
- Regression: listen/progress/admin endpoints should still work
"""
import requests
import sys

BASE_URL = "https://insight-hub-484.preview.emergentagent.com/api"

class AudioNarrationTester:
    def __init__(self):
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, passed, details=""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failed_tests.append(f"{name}: {details}")

    def test_admin_login(self):
        """Login as admin to get token for admin endpoints"""
        print("\n" + "="*60)
        print("STEP 1: Admin Login")
        print("="*60)
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": "admin@tradingnarrative.com", "password": "Admin@2025"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('token')
                self.log_test("Admin Login", True, f"Token: {self.admin_token[:20]}...")
                return True
            else:
                self.log_test("Admin Login", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, str(e))
            return False

    def test_uncached_essay_503(self):
        """Test uncached essay returns 503 with specific message (max 2 calls)"""
        print("\n" + "="*60)
        print("STEP 2: Uncached Essay (five-things) - Expect 503")
        print("="*60)
        print("⚠️  This essay is UNCACHED and ElevenLabs has 0 credits")
        print("   Calling at most 2 times to avoid hammering the API")
        
        slug = "five-things-commodity-desks-need-to-know-this-week"
        url = f"{BASE_URL}/posts/{slug}/audio?voice=male"
        
        try:
            response = requests.get(url, timeout=30)
            status = response.status_code
            
            print(f"   Status: {status}")
            
            if status == 503:
                # Check for specific message
                try:
                    data = response.json()
                    detail = data.get('detail', '')
                    print(f"   Detail: {detail}")
                    
                    if 'audio credits are being refilled' in detail:
                        self.log_test(
                            "Uncached Essay Returns 503 with Specific Message",
                            True,
                            f"Correct message: '{detail}'"
                        )
                        return True
                    else:
                        self.log_test(
                            "Uncached Essay Returns 503 with Specific Message",
                            False,
                            f"Wrong message: '{detail}' (expected 'audio credits are being refilled')"
                        )
                        return False
                except:
                    self.log_test(
                        "Uncached Essay Returns 503 with Specific Message",
                        False,
                        "Could not parse JSON response"
                    )
                    return False
            elif status == 502:
                self.log_test(
                    "Uncached Essay Returns 503 with Specific Message",
                    False,
                    "Got 502 (generic error) instead of 503 with specific message"
                )
                return False
            else:
                self.log_test(
                    "Uncached Essay Returns 503 with Specific Message",
                    False,
                    f"Got status {status} instead of 503"
                )
                return False
                
        except Exception as e:
            self.log_test("Uncached Essay Returns 503 with Specific Message", False, str(e))
            return False

    def test_cached_essay(self, slug, name):
        """Test a cached essay returns 200 with audio"""
        url = f"{BASE_URL}/posts/{slug}/audio?voice=male"
        
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            
            if status == 200:
                # Check headers
                cache_header = response.headers.get('X-Audio-Cache', '')
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.content)
                
                print(f"   Status: {status}")
                print(f"   Content-Type: {content_type}")
                print(f"   X-Audio-Cache: {cache_header}")
                print(f"   Size: {content_length / 1024 / 1024:.2f} MB")
                
                # Verify it's audio/mpeg
                if content_type != 'audio/mpeg':
                    self.log_test(
                        name,
                        False,
                        f"Wrong Content-Type: {content_type} (expected audio/mpeg)"
                    )
                    return False
                
                # Verify cache hit
                if cache_header != 'hit':
                    self.log_test(
                        name,
                        False,
                        f"X-Audio-Cache is '{cache_header}' (expected 'hit')"
                    )
                    return False
                
                # Verify reasonable size (should be ~2MB)
                if content_length < 100000:  # Less than 100KB is suspicious
                    self.log_test(
                        name,
                        False,
                        f"Audio too small: {content_length} bytes"
                    )
                    return False
                
                self.log_test(
                    name,
                    True,
                    f"200 OK, audio/mpeg, cache hit, {content_length / 1024 / 1024:.2f} MB"
                )
                return True
            else:
                try:
                    detail = response.json().get('detail', '')
                    self.log_test(name, False, f"Status {status}: {detail}")
                except:
                    self.log_test(name, False, f"Status {status}")
                return False
                
        except Exception as e:
            self.log_test(name, False, str(e))
            return False

    def test_all_cached_essays(self):
        """Test all cached essays"""
        print("\n" + "="*60)
        print("STEP 3: Cached Essays - Expect 200 with Audio")
        print("="*60)
        
        essays = [
            ("170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum", "170-kilometres (cached)"),
            ("the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a", "shipping-industry (cached)"),
            ("freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr", "freight-management (cached)"),
        ]
        
        results = []
        for slug, name in essays:
            print(f"\n   Testing: {name}")
            result = self.test_cached_essay(slug, name)
            results.append(result)
        
        return all(results)

    def test_listen_endpoint(self):
        """Test POST /api/posts/{slug}/audio/listen"""
        print("\n" + "="*60)
        print("STEP 4: Regression - Listen Endpoint")
        print("="*60)
        
        slug = "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        url = f"{BASE_URL}/posts/{slug}/audio/listen"
        
        try:
            response = requests.post(url, json={}, timeout=10)
            status = response.status_code
            
            if status == 200:
                data = response.json()
                if data.get('ok') == True:
                    self.log_test("Listen Endpoint", True, "Returns {ok: true}")
                    return True
                else:
                    self.log_test("Listen Endpoint", False, f"Response: {data}")
                    return False
            else:
                self.log_test("Listen Endpoint", False, f"Status {status}")
                return False
                
        except Exception as e:
            self.log_test("Listen Endpoint", False, str(e))
            return False

    def test_progress_endpoint(self):
        """Test POST /api/posts/{slug}/audio/progress"""
        print("\n" + "="*60)
        print("STEP 5: Regression - Progress Endpoint")
        print("="*60)
        
        slug = "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        url = f"{BASE_URL}/posts/{slug}/audio/progress"
        
        try:
            response = requests.post(url, json={"milestone": 25}, timeout=10)
            status = response.status_code
            
            if status == 200:
                data = response.json()
                if data.get('ok') == True:
                    self.log_test("Progress Endpoint", True, "Returns {ok: true}")
                    return True
                else:
                    self.log_test("Progress Endpoint", False, f"Response: {data}")
                    return False
            else:
                self.log_test("Progress Endpoint", False, f"Status {status}")
                return False
                
        except Exception as e:
            self.log_test("Progress Endpoint", False, str(e))
            return False

    def test_admin_narrations(self):
        """Test GET /api/admin/narrations"""
        print("\n" + "="*60)
        print("STEP 6: Regression - Admin Narrations Endpoint")
        print("="*60)
        
        if not self.admin_token:
            self.log_test("Admin Narrations", False, "No admin token")
            return False
        
        url = f"{BASE_URL}/admin/narrations"
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code
            
            if status == 200:
                data = response.json()
                essays = data.get('essays', [])
                print(f"   Found {len(essays)} essays")
                
                if len(essays) > 0:
                    self.log_test("Admin Narrations", True, f"Returns {len(essays)} essays")
                    return True
                else:
                    self.log_test("Admin Narrations", False, "Empty essays list")
                    return False
            else:
                self.log_test("Admin Narrations", False, f"Status {status}")
                return False
                
        except Exception as e:
            self.log_test("Admin Narrations", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("\n" + "="*80)
        print("AUDIO NARRATION BUG FIX - BACKEND TESTING")
        print("Testing ElevenLabs quota exhausted handling")
        print("="*80)
        
        # Step 1: Login
        if not self.test_admin_login():
            print("\n❌ Admin login failed, stopping tests")
            return False
        
        # Step 2: Test uncached essay (503 with specific message)
        self.test_uncached_essay_503()
        
        # Step 3: Test cached essays (200 with audio)
        self.test_all_cached_essays()
        
        # Step 4-6: Regression tests
        self.test_listen_endpoint()
        self.test_progress_endpoint()
        self.test_admin_narrations()
        
        # Print summary
        print("\n" + "="*80)
        print("BACKEND TEST RESULTS")
        print("="*80)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests ({len(self.failed_tests)}):")
            for failure in self.failed_tests:
                print(f"   - {failure}")
        else:
            print("\n✅ All backend tests passed!")
        
        print("="*80)
        
        return len(self.failed_tests) == 0

def main():
    tester = AudioNarrationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
