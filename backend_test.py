"""Backend API tests for The Trading Narrative - Bug Fix & Popular Highlights Feature"""
import requests
import sys

PREVIEW_URL = "https://insight-hub-484.preview.emergentagent.com"
PRODUCTION_URL = "https://thetradingnarrative.com"

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

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


def test_production_api_readonly(runner):
    """Test production API - READ ONLY (no modifications)"""
    print("\n" + "="*60)
    print("PRODUCTION API TESTS (READ-ONLY)")
    print("="*60)
    
    # Test 1: Edition #1 in briefings
    try:
        resp = requests.get(f"{PRODUCTION_URL}/api/briefings", timeout=10)
        briefings = resp.json().get("briefings", [])
        edition_1 = next((b for b in briefings if b.get("edition") == 1), None)
        runner.test(
            "Production: Edition #1 exists in /api/briefings",
            edition_1 is not None and "Five Things Commodity Desks Need to Know This Week" in edition_1.get("title", ""),
            f"Edition #1 not found or title mismatch. Found: {edition_1.get('title') if edition_1 else 'None'}"
        )
    except Exception as e:
        runner.test("Production: Edition #1 in briefings", False, str(e))

    # Test 2: Posts include Freight Management and Edition #1
    try:
        resp = requests.get(f"{PRODUCTION_URL}/api/posts?limit=5", timeout=10)
        posts = resp.json().get("posts", [])
        freight_post = next((p for p in posts if "freight-management" in p.get("slug", "").lower()), None)
        edition_post = next((p for p in posts if p.get("edition") == 1), None)
        
        runner.test(
            "Production: Freight Management article in /api/posts",
            freight_post is not None,
            f"Freight Management article not found in first 5 posts"
        )
        runner.test(
            "Production: Edition #1 post in /api/posts",
            edition_post is not None,
            f"Edition #1 post not found in first 5 posts"
        )
    except Exception as e:
        runner.test("Production: Posts check", False, str(e))


def test_preview_backend(runner):
    """Test preview environment backend"""
    print("\n" + "="*60)
    print("PREVIEW BACKEND TESTS")
    print("="*60)
    
    # Test 1: Edition #1 in briefings
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/briefings", timeout=10)
        briefings = resp.json().get("briefings", [])
        edition_1 = next((b for b in briefings if b.get("edition") == 1), None)
        runner.test(
            "Preview: Edition #1 in /api/briefings",
            edition_1 is not None,
            f"Edition #1 not found"
        )
    except Exception as e:
        runner.test("Preview: Edition #1 in briefings", False, str(e))

    # Test 2: Total published posts >= 11
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/posts", timeout=10)
        data = resp.json()
        total = data.get("total", 0)
        published = len([p for p in data.get("posts", []) if p.get("status") == "published"])
        runner.test(
            "Preview: Total posts >= 11",
            total >= 11,
            f"Expected >= 11, got {total}"
        )
        runner.test(
            "Preview: All posts published",
            published >= 11,
            f"Expected >= 11 published, got {published}"
        )
    except Exception as e:
        runner.test("Preview: Posts count", False, str(e))

    # Test 3: Popular highlights API - with highlights
    try:
        slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
        resp = requests.get(f"{PREVIEW_URL}/api/posts/{slug}/popular-highlights", timeout=10)
        data = resp.json()
        popular = data.get("popular", [])
        
        runner.test(
            "Preview: Popular highlights API returns data",
            len(popular) > 0,
            f"Expected highlights, got empty list"
        )
        
        if popular:
            first = popular[0]
            has_block_index = "block_index" in first
            has_text = "text" in first
            has_count = "count" in first
            correct_shape = has_block_index and has_text and has_count
            
            runner.test(
                "Preview: Popular highlights correct shape (block_index, text, count)",
                correct_shape,
                f"Missing fields. Has: {list(first.keys())}"
            )
            
            runner.test(
                "Preview: Popular highlights count >= 2",
                first.get("count", 0) >= 2,
                f"Expected count >= 2, got {first.get('count')}"
            )
            
            runner.test(
                "Preview: Popular highlights text matches",
                first.get("text") == "This is not a small firm problem.",
                f"Expected specific text, got: {first.get('text')}"
            )
    except Exception as e:
        runner.test("Preview: Popular highlights API", False, str(e))

    # Test 4: Popular highlights API - no highlights
    try:
        slug = "five-things-commodity-desks-need-to-know-this-week"
        resp = requests.get(f"{PREVIEW_URL}/api/posts/{slug}/popular-highlights", timeout=10)
        data = resp.json()
        popular = data.get("popular", [])
        
        runner.test(
            "Preview: Popular highlights empty for slug with no highlights",
            len(popular) == 0 and "popular" in data,
            f"Expected {{popular: []}}, got {data}"
        )
    except Exception as e:
        runner.test("Preview: Popular highlights empty", False, str(e))


def test_seed_code_review(runner):
    """Verify seed_database code sets status='draft' and views=0"""
    print("\n" + "="*60)
    print("SEED CODE REVIEW")
    print("="*60)
    
    try:
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
            
        # Check for status='draft' in seed
        has_draft_status = "'status': 'draft'" in content
        runner.test(
            "Seed code: Sets status='draft' for sample posts",
            has_draft_status,
            "status='draft' not found in seed_database"
        )
        
        # Check for views=0
        has_zero_views = "'views': 0" in content
        runner.test(
            "Seed code: Sets views=0 for sample posts",
            has_zero_views,
            "views=0 not found in seed_database"
        )
        
        # Check comment explaining the change
        has_comment = "Demo essays seed as DRAFTS" in content or "demo essays seed as drafts" in content.lower()
        runner.test(
            "Seed code: Has explanatory comment",
            has_comment,
            "Explanatory comment about draft seeding not found"
        )
    except Exception as e:
        runner.test("Seed code review", False, str(e))


def main():
    runner = TestRunner()
    
    print("\n" + "="*60)
    print("THE TRADING NARRATIVE - BACKEND API TESTS")
    print("Bug Fix Verification + Popular Highlights Feature")
    print("="*60)
    
    # Run all test suites
    test_production_api_readonly(runner)
    test_preview_backend(runner)
    test_seed_code_review(runner)
    
    # Print summary
    success = runner.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
