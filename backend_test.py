"""Backend API tests for The Trading Narrative - Narration Status Panel, Demo Cleanup, Admin Warm Trigger"""
import requests
import sys

PREVIEW_URL = "https://insight-hub-484.preview.emergentagent.com"
ADMIN_EMAIL = "admin@tradingnarrative.com"
ADMIN_PASSWORD = "Admin@2025"

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.admin_token = None

    def test(self, name, condition, error_msg=""):
        """Run a single test assertion"""
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"✅ PASS: {name}")
            return True
        else:
            self.tests_failed += 1
            self.failures.append(f"{name}: {error_msg}")
            print(f"❌ FAIL: {name}")
            if error_msg:
                print(f"   Error: {error_msg}")
            return False

    def summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {self.tests_run} | Passed: {self.tests_passed} | Failed: {self.tests_failed}")
        if self.failures:
            print(f"\nFailed Tests:")
            for f in self.failures:
                print(f"  - {f}")
        print(f"{'='*60}\n")
        return self.tests_failed == 0


def test_admin_login(runner):
    """Test admin login and get auth token"""
    print("\n" + "="*60)
    print("ADMIN LOGIN TEST")
    print("="*60)
    
    try:
        resp = requests.post(
            f"{PREVIEW_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        runner.test(
            "Admin login: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("token")
            runner.test(
                "Admin login: Token received",
                token is not None,
                "No token in response"
            )
            runner.admin_token = token
            print(f"   Admin token: {token[:20]}...")
        else:
            print(f"   Response: {resp.text}")
    except Exception as e:
        runner.test("Admin login", False, str(e))


def test_narrations_endpoint_auth(runner):
    """Test GET /api/admin/narrations with and without auth"""
    print("\n" + "="*60)
    print("NARRATIONS ENDPOINT - AUTH TESTS")
    print("="*60)
    
    # Test 1: Without auth should return 401/403
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/admin/narrations", timeout=10)
        runner.test(
            "Narrations without auth: Returns 401 or 403",
            resp.status_code in [401, 403],
            f"Expected 401 or 403, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Narrations without auth", False, str(e))
    
    # Test 2: With admin auth should return 200
    if not runner.admin_token:
        print("⚠️  Skipping authenticated tests - no admin token")
        return
    
    try:
        headers = {"Authorization": f"Bearer {runner.admin_token}"}
        resp = requests.get(f"{PREVIEW_URL}/api/admin/narrations", headers=headers, timeout=10)
        runner.test(
            "Narrations with auth: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Check enabled field
            runner.test(
                "Narrations: enabled is true",
                data.get("enabled") is True,
                f"Expected enabled=true, got {data.get('enabled')}"
            )
            
            # Check warming field (boolean)
            warming = data.get("warming")
            runner.test(
                "Narrations: warming is boolean",
                isinstance(warming, bool),
                f"Expected boolean, got {type(warming)}"
            )
            print(f"   warming: {warming}")
            
            # Check credits field (expected to be null due to missing user_read permission)
            credits = data.get("credits")
            runner.test(
                "Narrations: credits is null (expected - API key lacks user_read permission)",
                credits is None,
                f"Expected null, got {credits}"
            )
            
            # Check cached_count
            cached_count = data.get("cached_count")
            runner.test(
                "Narrations: cached_count is 3",
                cached_count == 3,
                f"Expected 3, got {cached_count}"
            )
            
            # Check total
            total = data.get("total")
            runner.test(
                "Narrations: total is 4",
                total == 4,
                f"Expected 4, got {total}"
            )
            
            # Check essays array
            essays = data.get("essays", [])
            runner.test(
                "Narrations: essays array has 4 items",
                len(essays) == 4,
                f"Expected 4 essays, got {len(essays)}"
            )
            
            # Check essay structure
            if essays:
                essay = essays[0]
                required_fields = ["slug", "title", "tier", "cached", "scopes", "bytes", "listens"]
                for field in required_fields:
                    runner.test(
                        f"Narrations: Essay has '{field}' field",
                        field in essay,
                        f"Missing field: {field}"
                    )
                
                # Count cached vs missing
                cached_essays = [e for e in essays if e.get("cached")]
                missing_essays = [e for e in essays if not e.get("cached")]
                print(f"   Cached essays: {len(cached_essays)}")
                print(f"   Missing essays: {len(missing_essays)}")
                
                # Check for the specific missing essay
                five_things_essay = next((e for e in essays if "five-things-commodity-desks" in e.get("slug", "")), None)
                if five_things_essay:
                    runner.test(
                        "Narrations: 'Five Things Commodity Desks' essay is Missing",
                        not five_things_essay.get("cached"),
                        f"Expected cached=false, got {five_things_essay.get('cached')}"
                    )
                    print(f"   Five Things essay: {five_things_essay.get('title')[:50]}... - cached={five_things_essay.get('cached')}")
        else:
            print(f"   Response: {resp.text}")
    except Exception as e:
        runner.test("Narrations with auth", False, str(e))


def test_warm_endpoint(runner):
    """Test POST /api/admin/narrations/warm (call ONCE only)"""
    print("\n" + "="*60)
    print("WARM ENDPOINT TEST (CALLING ONCE)")
    print("="*60)
    
    if not runner.admin_token:
        print("⚠️  Skipping warm test - no admin token")
        return
    
    try:
        headers = {"Authorization": f"Bearer {runner.admin_token}"}
        resp = requests.post(f"{PREVIEW_URL}/api/admin/narrations/warm", headers=headers, timeout=10)
        runner.test(
            "Warm endpoint: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            runner.test(
                "Warm endpoint: ok is true",
                data.get("ok") is True,
                f"Expected ok=true, got {data.get('ok')}"
            )
            
            runner.test(
                "Warm endpoint: started is true",
                data.get("started") is True,
                f"Expected started=true, got {data.get('started')}"
            )
            
            print(f"   Response: {data}")
            print("   ⚠️  Expected: Warmup will try to generate missing essay and stop with quota error (0 credits)")
            
            # Wait a moment and check if warming flag is set
            import time
            time.sleep(2)
            
            resp2 = requests.get(f"{PREVIEW_URL}/api/admin/narrations", headers=headers, timeout=10)
            if resp2.status_code == 200:
                data2 = resp2.json()
                warming = data2.get("warming")
                print(f"   After warmup call, warming={warming} (may briefly be true)")
        else:
            print(f"   Response: {resp.text}")
    except Exception as e:
        runner.test("Warm endpoint", False, str(e))


def test_demo_cleanup(runner):
    """Test demo cleanup - verify only 4 published posts"""
    print("\n" + "="*60)
    print("DEMO CLEANUP TEST")
    print("="*60)
    
    # Test 1: GET /api/posts returns exactly 4 posts
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/posts", timeout=10)
        runner.test(
            "Demo cleanup: /api/posts returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            posts = data.get("posts", [])
            
            runner.test(
                "Demo cleanup: Exactly 4 published posts",
                len(posts) == 4,
                f"Expected 4 posts, got {len(posts)}"
            )
            
            # Check that none of the demo titles are present
            demo_titles = [
                "The Deep Work Reset",
                "Why Great Products Die in Distribution",
                "The Attention Economy",
                "Building in Public",
                "The Creator Economy"
            ]
            
            post_titles = [p.get("title", "") for p in posts]
            has_demo_titles = any(demo in title for demo in demo_titles for title in post_titles)
            
            runner.test(
                "Demo cleanup: No demo essay titles in published posts",
                not has_demo_titles,
                f"Found demo titles in: {post_titles}"
            )
            
            print(f"   Published posts:")
            for p in posts:
                print(f"     - {p.get('title')[:60]}...")
    except Exception as e:
        runner.test("Demo cleanup: /api/posts", False, str(e))
    
    # Test 2: Check admin posts to verify demo essays are drafts
    if not runner.admin_token:
        print("⚠️  Skipping admin posts check - no admin token")
        return
    
    try:
        headers = {"Authorization": f"Bearer {runner.admin_token}"}
        resp = requests.get(f"{PREVIEW_URL}/api/admin/posts", headers=headers, timeout=10)
        runner.test(
            "Demo cleanup: /api/admin/posts returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            all_posts = data.get("posts", [])
            
            # Count published vs draft
            published = [p for p in all_posts if p.get("status") == "published"]
            drafts = [p for p in all_posts if p.get("status") == "draft"]
            
            print(f"   Total posts: {len(all_posts)}")
            print(f"   Published: {len(published)}")
            print(f"   Drafts: {len(drafts)}")
            
            runner.test(
                "Demo cleanup: Exactly 4 published posts in admin view",
                len(published) == 4,
                f"Expected 4 published, got {len(published)}"
            )
            
            # Check that demo essays are in drafts
            demo_keywords = ["Deep Work", "Distribution", "Attention Economy"]
            draft_titles = [p.get("title", "") for p in drafts]
            has_demo_in_drafts = any(keyword in title for keyword in demo_keywords for title in draft_titles)
            
            if has_demo_in_drafts:
                print(f"   ✓ Demo essays found in drafts (as expected)")
    except Exception as e:
        runner.test("Demo cleanup: /api/admin/posts", False, str(e))


def test_regression_endpoints(runner):
    """Test that existing endpoints still work"""
    print("\n" + "="*60)
    print("REGRESSION TESTS")
    print("="*60)
    
    # Test 1: /api/posts still works
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/posts?limit=5", timeout=10)
        runner.test(
            "Regression: /api/posts returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Regression: /api/posts", False, str(e))
    
    # Test 2: /api/categories still works
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/categories", timeout=10)
        runner.test(
            "Regression: /api/categories returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Regression: /api/categories", False, str(e))
    
    # Test 3: /api/briefings still works
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/briefings", timeout=10)
        runner.test(
            "Regression: /api/briefings returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Regression: /api/briefings", False, str(e))
    
    # Test 4: /api/admin/analytics/stats still works (with auth)
    if not runner.admin_token:
        print("⚠️  Skipping analytics test - no admin token")
        return
    
    try:
        headers = {"Authorization": f"Bearer {runner.admin_token}"}
        resp = requests.get(f"{PREVIEW_URL}/api/admin/analytics/stats", headers=headers, timeout=10)
        runner.test(
            "Regression: /api/admin/analytics/stats returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Check that listens and listens_7d fields are present
            runner.test(
                "Regression: Stats has 'listens' field",
                "listens" in data,
                "Missing 'listens' field"
            )
            
            runner.test(
                "Regression: Stats has 'listens_7d' field",
                "listens_7d" in data,
                "Missing 'listens_7d' field"
            )
            
            print(f"   listens: {data.get('listens')}")
            print(f"   listens_7d: {data.get('listens_7d')}")
    except Exception as e:
        runner.test("Regression: /api/admin/analytics/stats", False, str(e))


def main():
    runner = TestRunner()
    
    print("\n" + "="*60)
    print("THE TRADING NARRATIVE - BACKEND API TESTS")
    print("Narration Status Panel, Demo Cleanup, Admin Warm Trigger")
    print("="*60)
    
    # Run all test suites
    test_admin_login(runner)
    test_narrations_endpoint_auth(runner)
    test_warm_endpoint(runner)
    test_demo_cleanup(runner)
    test_regression_endpoints(runner)
    
    # Print summary
    success = runner.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
