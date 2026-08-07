"""
Backend test for Narration Health Alert feature
READ-ONLY: Does not modify audio_cache or posts
"""
import requests
import sys

BASE_URL = "https://insight-hub-484.preview.emergentagent.com"

class NarrationHealthTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []

    def log(self, message, is_error=False):
        prefix = "❌" if is_error else "✅"
        print(f"{prefix} {message}")
        if is_error:
            self.issues.append(message)

    def test_login(self):
        """Login as admin"""
        self.tests_run += 1
        print("\n🔍 Testing admin login...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "admin@tradingnarrative.com", "password": "Admin@2025"}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                if self.token:
                    self.tests_passed += 1
                    self.log("Admin login successful")
                    return True
                else:
                    self.log("Login response missing token", True)
                    return False
            else:
                self.log(f"Login failed with status {response.status_code}: {response.text}", True)
                return False
        except Exception as e:
            self.log(f"Login error: {str(e)}", True)
            return False

    def test_narrations_endpoint(self):
        """Test GET /api/admin/narrations"""
        self.tests_run += 1
        print("\n🔍 Testing GET /api/admin/narrations...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/admin/narrations", headers=headers)
            
            if response.status_code != 200:
                self.log(f"Narrations endpoint returned {response.status_code}: {response.text}", True)
                return False
            
            data = response.json()
            self.log(f"Narrations endpoint returned 200")
            
            # Check required fields
            required_fields = ['enabled', 'credits', 'cached_count', 'total', 'issues', 'essays']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                self.log(f"Missing required fields: {missing_fields}", True)
                return False
            
            self.log(f"All required fields present: {required_fields}")
            
            # Check issues array
            issues = data.get('issues', [])
            print(f"\n📊 Issues array: {len(issues)} entries")
            for issue in issues:
                print(f"   - {issue.get('title', 'N/A')}: {issue.get('problem', 'N/A')} (slug: {issue.get('slug', 'N/A')})")
            
            if len(issues) != 2:
                self.log(f"Expected 2 issues, got {len(issues)}", True)
                return False
            
            self.log(f"Issues array has exactly 2 entries")
            
            # Check that all issues have required fields
            found_slugs = [i.get('slug') for i in issues]
            self.log(f"Problem essays: {', '.join(found_slugs)}")
            
            # Check all issues have 'missing' problem
            for issue in issues:
                if issue.get('problem') != 'missing':
                    self.log(f"Expected problem='missing', got '{issue.get('problem')}' for {issue.get('slug')}", True)
                    return False
            
            self.log(f"All issues have problem='missing'")
            
            # Check essays array
            essays = data.get('essays', [])
            print(f"\n📊 Essays array: {len(essays)} entries")
            
            if len(essays) != 4:
                self.log(f"Expected 4 essays, got {len(essays)}", True)
                return False
            
            self.log(f"Essays array has 4 entries")
            
            # Check health fields for specific essays
            essay_health = {}
            for essay in essays:
                slug = essay.get('slug')
                health = essay.get('health')
                cached = essay.get('cached')
                print(f"   - {essay.get('title', 'N/A')[:50]}: health={health}, cached={cached}")
                essay_health[slug] = health
            
            # Verify that we have 2 'ok' and 2 'missing' health statuses
            health_counts = {}
            for health in essay_health.values():
                health_counts[health] = health_counts.get(health, 0) + 1
            
            if health_counts.get('ok') != 2:
                self.log(f"Expected 2 essays with health='ok', got {health_counts.get('ok', 0)}", True)
                return False
            
            if health_counts.get('missing') != 2:
                self.log(f"Expected 2 essays with health='missing', got {health_counts.get('missing', 0)}", True)
                return False
            
            self.log(f"Essay health distribution correct: 2 ok, 2 missing")
            
            # Check regression fields
            if data.get('cached_count') != 2:
                self.log(f"Expected cached_count=2, got {data.get('cached_count')}", True)
                return False
            
            self.log(f"cached_count=2 (regression check passed)")
            
            if data.get('total') != 4:
                self.log(f"Expected total=4, got {data.get('total')}", True)
                return False
            
            self.log(f"total=4 (regression check passed)")
            
            # Check that essays have completion and milestones
            for essay in essays:
                if 'completion' not in essay or 'milestones' not in essay:
                    self.log(f"Essay {essay.get('slug')} missing completion or milestones fields", True)
                    return False
            
            self.log(f"All essays have completion and milestones fields (regression check passed)")
            
            self.tests_passed += 1
            return True
            
        except Exception as e:
            self.log(f"Narrations endpoint error: {str(e)}", True)
            return False

    def test_analytics_stats(self):
        """Test GET /api/admin/analytics/stats (regression)"""
        self.tests_run += 1
        print("\n🔍 Testing GET /api/admin/analytics/stats (regression)...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{BASE_URL}/api/admin/analytics/stats", headers=headers)
            
            if response.status_code != 200:
                self.log(f"Analytics stats endpoint returned {response.status_code}", True)
                return False
            
            data = response.json()
            required_fields = ['pageviews', 'listens', 'newsletter_subscribers', 'users', 'premium_subscribers']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                self.log(f"Analytics stats missing fields: {missing_fields}", True)
                return False
            
            self.log(f"Analytics stats endpoint working (regression check passed)")
            self.tests_passed += 1
            return True
            
        except Exception as e:
            self.log(f"Analytics stats error: {str(e)}", True)
            return False

    def test_cached_audio(self):
        """Test GET cached audio (regression)"""
        self.tests_run += 1
        print("\n🔍 Testing GET cached audio (regression)...")
        try:
            # Test the shipping essay which should have cached audio
            response = requests.get(
                f"{BASE_URL}/api/posts/the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a/audio?voice=male"
            )
            
            if response.status_code != 200:
                self.log(f"Cached audio endpoint returned {response.status_code}", True)
                return False
            
            # Check for cache hit header
            cache_header = response.headers.get('X-Audio-Cache')
            if cache_header != 'hit':
                self.log(f"Expected X-Audio-Cache: hit, got '{cache_header}'", True)
                return False
            
            self.log(f"Cached audio endpoint working with X-Audio-Cache: hit (regression check passed)")
            self.tests_passed += 1
            return True
            
        except Exception as e:
            self.log(f"Cached audio error: {str(e)}", True)
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("NARRATION HEALTH ALERT - BACKEND TESTS (READ-ONLY)")
        print("=" * 60)
        
        if not self.test_login():
            print("\n❌ Cannot proceed without admin login")
            return False
        
        self.test_narrations_endpoint()
        self.test_analytics_stats()
        self.test_cached_audio()
        
        print("\n" + "=" * 60)
        print(f"📊 RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print("=" * 60)
        
        if self.issues:
            print("\n❌ ISSUES FOUND:")
            for issue in self.issues:
                print(f"   - {issue}")
        
        return self.tests_passed == self.tests_run


def main():
    tester = NarrationHealthTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
