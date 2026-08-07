"""Backend API tests for The Trading Narrative - Series, Share, and Audio Features"""
import requests
import sys
import re

PREVIEW_URL = "https://insight-hub-484.preview.emergentagent.com"

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


def test_series_endpoints(runner):
    """Test editorial series endpoints"""
    print("\n" + "="*60)
    print("SERIES ENDPOINTS TESTS")
    print("="*60)
    
    # Test 1: GET /api/series returns trading-operations with count 3
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/series", timeout=10)
        runner.test(
            "Series list: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        data = resp.json()
        series_list = data.get("series", [])
        
        runner.test(
            "Series list: Returns 1 series",
            len(series_list) == 1,
            f"Expected 1 series, got {len(series_list)}"
        )
        
        if series_list:
            s = series_list[0]
            runner.test(
                "Series list: Slug is 'trading-operations'",
                s.get("slug") == "trading-operations",
                f"Expected 'trading-operations', got {s.get('slug')}"
            )
            runner.test(
                "Series list: Title is 'Trading Operations'",
                s.get("title") == "Trading Operations",
                f"Expected 'Trading Operations', got {s.get('title')}"
            )
            runner.test(
                "Series list: Count is 3",
                s.get("count") == 3,
                f"Expected count 3, got {s.get('count')}"
            )
    except Exception as e:
        runner.test("Series list endpoint", False, str(e))

    # Test 2: GET /api/series/trading-operations returns posts in exact order
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/series/trading-operations", timeout=10)
        runner.test(
            "Series detail: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        data = resp.json()
        posts = data.get("posts", [])
        
        runner.test(
            "Series detail: Returns 3 posts",
            len(posts) == 3,
            f"Expected 3 posts, got {len(posts)}"
        )
        
        expected_order = [
            "five-things-commodity-desks-need-to-know-this-week",
            "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
            "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a"
        ]
        
        if len(posts) >= 3:
            actual_order = [p.get("slug") for p in posts[:3]]
            runner.test(
                "Series detail: Post 1 is 'Five Things Commodity Desks...'",
                actual_order[0] == expected_order[0],
                f"Expected {expected_order[0]}, got {actual_order[0]}"
            )
            runner.test(
                "Series detail: Post 2 is 'Freight Management...'",
                actual_order[1] == expected_order[1],
                f"Expected {expected_order[1]}, got {actual_order[1]}"
            )
            runner.test(
                "Series detail: Post 3 is 'The Shipping Industry...'",
                actual_order[2] == expected_order[2],
                f"Expected {expected_order[2]}, got {actual_order[2]}"
            )
    except Exception as e:
        runner.test("Series detail endpoint", False, str(e))

    # Test 3: GET /api/series/unknown returns 404
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/series/unknown-series", timeout=10)
        runner.test(
            "Series 404: Unknown series returns 404",
            resp.status_code == 404,
            f"Expected 404, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Series 404 test", False, str(e))


def test_posts_with_series(runner):
    """Test posts include series information"""
    print("\n" + "="*60)
    print("POSTS WITH SERIES INFO TESTS")
    print("="*60)
    
    # Test 1: Freight article includes series info
    try:
        slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
        resp = requests.get(f"{PREVIEW_URL}/api/posts/{slug}", timeout=10)
        runner.test(
            "Post with series: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        data = resp.json()
        series = data.get("series")
        
        runner.test(
            "Post with series: Has series field",
            series is not None,
            "Expected series field, got None"
        )
        
        if series:
            runner.test(
                "Post with series: Slug is 'trading-operations'",
                series.get("slug") == "trading-operations",
                f"Expected 'trading-operations', got {series.get('slug')}"
            )
            runner.test(
                "Post with series: Title is 'Trading Operations'",
                series.get("title") == "Trading Operations",
                f"Expected 'Trading Operations', got {series.get('title')}"
            )
    except Exception as e:
        runner.test("Post with series info", False, str(e))

    # Test 2: Non-series article has series=null
    try:
        slug = "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        resp = requests.get(f"{PREVIEW_URL}/api/posts/{slug}", timeout=10)
        runner.test(
            "Post without series: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        data = resp.json()
        series = data.get("series")
        
        runner.test(
            "Post without series: series is None",
            series is None,
            f"Expected None, got {series}"
        )
    except Exception as e:
        runner.test("Post without series info", False, str(e))


def test_share_endpoint(runner):
    """Test LinkedIn/X preview card endpoint"""
    print("\n" + "="*60)
    print("SHARE ENDPOINT (OG CARDS) TESTS")
    print("="*60)
    
    # Test 1: Valid slug returns HTML with OG tags
    try:
        slug = "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a"
        resp = requests.get(f"{PREVIEW_URL}/api/share/{slug}", timeout=10)
        runner.test(
            "Share endpoint: Status 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
        
        html = resp.text
        
        # Check for og:title
        has_og_title = 'property="og:title"' in html and "The Shipping Industry" in html
        runner.test(
            "Share endpoint: Contains og:title with essay title",
            has_og_title,
            "og:title not found or doesn't contain essay title"
        )
        
        # Check for og:image
        has_og_image = 'property="og:image"' in html and 'unsplash.com' in html
        runner.test(
            "Share endpoint: Contains og:image with unsplash URL",
            has_og_image,
            "og:image not found or doesn't contain unsplash URL"
        )
        
        # Check for og:url
        has_og_url = 'property="og:url"' in html and f'/post/{slug}' in html
        runner.test(
            "Share endpoint: Contains og:url ending in /post/[slug]",
            has_og_url,
            f"og:url not found or doesn't end with /post/{slug}"
        )
        
        # Check for twitter:card
        has_twitter_card = 'name="twitter:card"' in html and 'summary_large_image' in html
        runner.test(
            "Share endpoint: Contains twitter:card summary_large_image",
            has_twitter_card,
            "twitter:card summary_large_image not found"
        )
        
        # Check for meta refresh redirect
        has_meta_refresh = 'http-equiv="refresh"' in html and f'/post/{slug}' in html
        runner.test(
            "Share endpoint: Contains meta refresh redirect",
            has_meta_refresh,
            "meta refresh redirect not found"
        )
        
        # Check for JS redirect
        has_js_redirect = 'window.location.replace' in html and f'/post/{slug}' in html
        runner.test(
            "Share endpoint: Contains JS redirect",
            has_js_redirect,
            "window.location.replace redirect not found"
        )
        
    except Exception as e:
        runner.test("Share endpoint valid slug", False, str(e))

    # Test 2: Unknown slug returns 404
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/share/unknown-slug-12345", timeout=10)
        runner.test(
            "Share endpoint 404: Unknown slug returns 404",
            resp.status_code == 404,
            f"Expected 404, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Share endpoint 404 test", False, str(e))


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
        
        data = resp.json()
        runner.test(
            "Regression: /api/posts has posts array",
            "posts" in data and isinstance(data["posts"], list),
            "posts array not found"
        )
    except Exception as e:
        runner.test("Regression: /api/posts", False, str(e))

    # Test 2: /api/briefings still works
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/briefings", timeout=10)
        runner.test(
            "Regression: /api/briefings returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Regression: /api/briefings", False, str(e))

    # Test 3: /api/categories still works
    try:
        resp = requests.get(f"{PREVIEW_URL}/api/categories", timeout=10)
        runner.test(
            "Regression: /api/categories returns 200",
            resp.status_code == 200,
            f"Expected 200, got {resp.status_code}"
        )
    except Exception as e:
        runner.test("Regression: /api/categories", False, str(e))


def main():
    runner = TestRunner()
    
    print("\n" + "="*60)
    print("THE TRADING NARRATIVE - BACKEND API TESTS")
    print("Series, Share (OG Cards), and Audio Features")
    print("="*60)
    
    # Run all test suites
    test_series_endpoints(runner)
    test_posts_with_series(runner)
    test_share_endpoint(runner)
    test_regression_endpoints(runner)
    
    # Print summary
    success = runner.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
