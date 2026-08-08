"""
Test suite for new essay import and briefing tier change.

Tests:
1. New essay "delivering-a-power-trading-desk..." with premium tier, delivery category
2. Briefing "five-things-commodity-desks..." changed to premium
3. Server-side paywall enforcement (3 blocks for anonymous, full for entitled)
4. Regression: free essays still accessible, analytics working
"""
import requests
import sys

BASE_URL = "https://insight-hub-484.preview.emergentagent.com"
ADMIN_EMAIL = "admin@tradingnarrative.com"
ADMIN_PASSWORD = "Admin@2025"

class TestNewEssayImport:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def log_test(self, name, passed, details=""):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {name}")
            if details:
                print(f"   {details}")
        else:
            self.failures.append({"test": name, "details": details})
            print(f"❌ FAIL: {name}")
            print(f"   {details}")

    def admin_login(self):
        """Login as admin to get token"""
        print("\n🔐 Logging in as admin...")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                print(f"✅ Admin login successful")
                return True
            else:
                print(f"❌ Admin login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False

    def test_new_essay_anonymous(self):
        """Test new essay without authentication - should be locked with 3 blocks"""
        print("\n📝 Testing new essay (anonymous)...")
        slug = "delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile"
        
        try:
            response = requests.get(f"{self.base_url}/api/posts/{slug}", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "New essay - anonymous access",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            
            # Check tier
            tier_ok = data.get("tier") == "premium"
            self.log_test(
                "New essay - tier is premium",
                tier_ok,
                f"tier={data.get('tier')}"
            )
            
            # Check category
            category_ok = data.get("category") == "delivery"
            self.log_test(
                "New essay - category is delivery",
                category_ok,
                f"category={data.get('category')}"
            )
            
            # Check is_locked
            locked_ok = data.get("is_locked") == True
            self.log_test(
                "New essay - is_locked is true",
                locked_ok,
                f"is_locked={data.get('is_locked')}"
            )
            
            # Check content_blocks count (EXACTLY 3 for paywall)
            blocks = data.get("content_blocks", [])
            blocks_ok = len(blocks) == 3
            self.log_test(
                "New essay - exactly 3 preview blocks",
                blocks_ok,
                f"Got {len(blocks)} blocks (expected 3)"
            )
            
            # Check shown_blocks
            shown_ok = data.get("shown_blocks") == 3
            self.log_test(
                "New essay - shown_blocks is 3",
                shown_ok,
                f"shown_blocks={data.get('shown_blocks')}"
            )
            
            # Check total_blocks (should be 113)
            total_ok = data.get("total_blocks") == 113
            self.log_test(
                "New essay - total_blocks is 113",
                total_ok,
                f"total_blocks={data.get('total_blocks')}"
            )
            
            # Verify full essay text is NOT present
            full_text = " ".join(blocks)
            leak_check = "Part 8: A Compliance-by-Design Checklist" not in full_text
            self.log_test(
                "New essay - no content leak (Part 8 not in preview)",
                leak_check,
                "Full essay content properly restricted"
            )
            
            return tier_ok and category_ok and locked_ok and blocks_ok
            
        except Exception as e:
            self.log_test("New essay - anonymous access", False, f"Error: {e}")
            return False

    def test_new_essay_admin(self):
        """Test new essay with admin token - should be unlocked with 113 blocks"""
        print("\n📝 Testing new essay (admin/entitled)...")
        slug = "delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile"
        
        if not self.admin_token:
            self.log_test("New essay - admin access", False, "No admin token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/posts/{slug}",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "New essay - admin access",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            
            # Check is_locked (should be false for entitled user)
            unlocked_ok = data.get("is_locked") == False
            self.log_test(
                "New essay - is_locked is false for admin",
                unlocked_ok,
                f"is_locked={data.get('is_locked')}"
            )
            
            # Check content_blocks count (should be 113)
            blocks = data.get("content_blocks", [])
            blocks_ok = len(blocks) == 113
            self.log_test(
                "New essay - 113 full blocks for admin",
                blocks_ok,
                f"Got {len(blocks)} blocks (expected 113)"
            )
            
            # Verify deep section is present
            full_text = " ".join(blocks)
            deep_section_ok = "Part 7: Delivery Anti-Patterns Specific to Power" in full_text
            self.log_test(
                "New essay - deep section visible to admin",
                deep_section_ok,
                "Part 7 section found in full content"
            )
            
            return unlocked_ok and blocks_ok and deep_section_ok
            
        except Exception as e:
            self.log_test("New essay - admin access", False, f"Error: {e}")
            return False

    def test_briefing_premium(self):
        """Test briefing is now premium (anonymous should see paywall)"""
        print("\n📰 Testing briefing tier change...")
        slug = "five-things-commodity-desks-need-to-know-this-week"
        
        try:
            response = requests.get(f"{self.base_url}/api/posts/{slug}", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Briefing - anonymous access",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            
            # Check tier is premium
            tier_ok = data.get("tier") == "premium"
            self.log_test(
                "Briefing - tier is premium",
                tier_ok,
                f"tier={data.get('tier')}"
            )
            
            # Check is_locked
            locked_ok = data.get("is_locked") == True
            self.log_test(
                "Briefing - is_locked is true",
                locked_ok,
                f"is_locked={data.get('is_locked')}"
            )
            
            # Check only 3 preview blocks
            blocks = data.get("content_blocks", [])
            blocks_ok = len(blocks) == 3
            self.log_test(
                "Briefing - exactly 3 preview blocks",
                blocks_ok,
                f"Got {len(blocks)} blocks (expected 3)"
            )
            
            return tier_ok and locked_ok and blocks_ok
            
        except Exception as e:
            self.log_test("Briefing - anonymous access", False, f"Error: {e}")
            return False

    def test_category_delivery(self):
        """Test GET /api/posts?category=delivery includes new essay"""
        print("\n📂 Testing category=delivery...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/posts?category=delivery",
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "Category delivery - list",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            posts = data.get("posts", [])
            slugs = [p.get("slug") for p in posts]
            
            new_essay_slug = "delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile"
            found = new_essay_slug in slugs
            
            self.log_test(
                "Category delivery - includes new essay",
                found,
                f"Found {len(posts)} posts in delivery category"
            )
            
            return found
            
        except Exception as e:
            self.log_test("Category delivery - list", False, f"Error: {e}")
            return False

    def test_posts_list(self):
        """Test GET /api/posts shows published posts"""
        print("\n📋 Testing posts list...")
        
        try:
            response = requests.get(f"{self.base_url}/api/posts", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Posts list",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            posts = data.get("posts", [])
            total = data.get("total", 0)
            
            # Check we have published posts (should be 5 according to requirements)
            count_ok = total >= 5
            self.log_test(
                "Posts list - at least 5 published",
                count_ok,
                f"Found {total} published posts"
            )
            
            # Check new essay is in the list
            slugs = [p.get("slug") for p in posts]
            new_essay_slug = "delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile"
            found = new_essay_slug in slugs
            
            self.log_test(
                "Posts list - includes new essay",
                found,
                f"New essay present in posts list"
            )
            
            return count_ok and found
            
        except Exception as e:
            self.log_test("Posts list", False, f"Error: {e}")
            return False

    def test_free_essay_regression(self):
        """Test free essay is still fully readable (regression check)"""
        print("\n🆓 Testing free essay regression...")
        # Using the freight management essay which should be free
        slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
        
        try:
            response = requests.get(f"{self.base_url}/api/posts/{slug}", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Free essay - access",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            
            # Check tier is free
            tier_ok = data.get("tier") == "free"
            self.log_test(
                "Free essay - tier is free",
                tier_ok,
                f"tier={data.get('tier')}"
            )
            
            # Check is NOT locked
            unlocked_ok = data.get("is_locked") == False
            self.log_test(
                "Free essay - is_locked is false",
                unlocked_ok,
                f"is_locked={data.get('is_locked')}"
            )
            
            # Check has full content
            blocks = data.get("content_blocks", [])
            has_content = len(blocks) > 10
            self.log_test(
                "Free essay - has full content",
                has_content,
                f"Got {len(blocks)} blocks"
            )
            
            return tier_ok and unlocked_ok and has_content
            
        except Exception as e:
            self.log_test("Free essay - access", False, f"Error: {e}")
            return False

    def test_analytics_stats(self):
        """Test GET /api/admin/analytics/stats works"""
        print("\n📊 Testing analytics stats...")
        
        if not self.admin_token:
            self.log_test("Analytics stats", False, "No admin token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/admin/analytics/stats",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test(
                    "Analytics stats",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            
            # Check response has expected fields
            has_stats = "total_views" in data or "posts" in data or "users" in data
            self.log_test(
                "Analytics stats - returns data",
                has_stats,
                f"Response keys: {list(data.keys())}"
            )
            
            return has_stats
            
        except Exception as e:
            self.log_test("Analytics stats", False, f"Error: {e}")
            return False

    def test_homepage_loads(self):
        """Test homepage loads (regression)"""
        print("\n🏠 Testing homepage...")
        
        try:
            response = requests.get(f"{self.base_url}/api/posts?featured=true", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Homepage - featured posts",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
                return False
            
            data = response.json()
            posts = data.get("posts", [])
            
            self.log_test(
                "Homepage - featured posts load",
                True,
                f"Found {len(posts)} featured posts"
            )
            
            return True
            
        except Exception as e:
            self.log_test("Homepage - featured posts", False, f"Error: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("BACKEND TEST SUITE: New Essay Import & Briefing Tier Change")
        print("=" * 70)
        
        # Login first
        if not self.admin_login():
            print("\n❌ Cannot proceed without admin login")
            return False
        
        # Run all tests
        self.test_new_essay_anonymous()
        self.test_new_essay_admin()
        self.test_briefing_premium()
        self.test_category_delivery()
        self.test_posts_list()
        self.test_free_essay_regression()
        self.test_analytics_stats()
        self.test_homepage_loads()
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failures)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n❌ FAILED TESTS:")
            for f in self.failures:
                print(f"  • {f['test']}")
                print(f"    {f['details']}")
        
        return len(self.failures) == 0


def main():
    tester = TestNewEssayImport()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
