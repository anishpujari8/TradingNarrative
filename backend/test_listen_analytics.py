import requests
import sys

class ListenAnalyticsTester:
    def __init__(self, base_url="https://insight-hub-484.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, check_headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        if self.admin_token and 'Authorization' not in req_headers:
            req_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check response headers if specified
                if check_headers:
                    for header_name, expected_value in check_headers.items():
                        actual_value = response.headers.get(header_name)
                        if actual_value == expected_value:
                            print(f"   ✅ Header {header_name}: {actual_value}")
                        else:
                            print(f"   ⚠️  Header {header_name}: expected '{expected_value}', got '{actual_value}'")
                            self.failed_tests.append(f"{name}: Header {header_name} mismatch")
                
                try:
                    return success, response.json(), response
                except:
                    return success, {}, response
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}, None

    def test_admin_login(self):
        """Test admin login and get token"""
        print("\n" + "="*60)
        print("TESTING: Admin Authentication")
        print("="*60)
        success, response, _ = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@tradingnarrative.com", "password": "Admin@2025"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_author_normalization(self):
        """Test that all posts have author.name = 'Anish Pujari'"""
        print("\n" + "="*60)
        print("TESTING: Author Normalization (All posts by Anish Pujari)")
        print("="*60)
        
        success, response, _ = self.run_test(
            "GET /api/posts (public list)",
            "GET",
            "posts?limit=100",
            200,
            headers={'Authorization': ''}  # No auth needed
        )
        
        if success:
            posts = response.get('posts', [])
            print(f"   Found {len(posts)} posts")
            
            if len(posts) == 0:
                print("   ⚠️  No posts found")
                self.failed_tests.append("Author Normalization: No posts found")
                return False
            
            # Check each post's author
            non_anish_posts = []
            for post in posts:
                author = post.get('author', {})
                author_name = author.get('name', '')
                if author_name != 'Anish Pujari':
                    non_anish_posts.append({
                        'title': post.get('title', 'Unknown'),
                        'author': author_name
                    })
            
            if len(non_anish_posts) == 0:
                print(f"   ✅ All {len(posts)} posts have author.name = 'Anish Pujari'")
                return True
            else:
                print(f"   ❌ Found {len(non_anish_posts)} posts with incorrect author:")
                for p in non_anish_posts[:5]:  # Show first 5
                    print(f"      - '{p['title'][:50]}' by '{p['author']}'")
                self.failed_tests.append(f"Author Normalization: {len(non_anish_posts)} posts have wrong author")
                return False
        
        return False

    def test_listen_analytics_valid_slug(self):
        """Test POST /api/posts/{valid-slug}/audio/listen"""
        print("\n" + "="*60)
        print("TESTING: Listen Analytics - Valid Slug")
        print("="*60)
        
        # Use a real published post slug
        slug = "the-ai-infrastructure-gold-rush-who-actually-wins"
        
        # Get initial listens count
        print(f"\n   Step 1: Get initial listens count for '{slug}'")
        success1, response1, _ = self.run_test(
            f"GET /api/posts/{slug}",
            "GET",
            f"posts/{slug}",
            200,
            headers={'Authorization': ''}
        )
        
        initial_listens = 0
        if success1:
            initial_listens = response1.get('listens', 0)
            print(f"   Initial listens: {initial_listens}")
        
        # Track a listen (anonymous, no auth)
        print(f"\n   Step 2: Track a listen (POST /api/posts/{slug}/audio/listen)")
        success2, response2, _ = self.run_test(
            "Track Listen (anonymous)",
            "POST",
            f"posts/{slug}/audio/listen",
            200,
            headers={'Authorization': ''}
        )
        
        if success2:
            if response2.get('ok') == True:
                print("   ✅ Response: {ok: true}")
            else:
                print(f"   ⚠️  Response: {response2}")
                self.failed_tests.append("Listen Analytics: Response not {ok: true}")
        
        # Verify listens incremented
        print(f"\n   Step 3: Verify listens incremented")
        success3, response3, _ = self.run_test(
            f"GET /api/posts/{slug} (verify increment)",
            "GET",
            f"posts/{slug}",
            200,
            headers={'Authorization': ''}
        )
        
        if success3:
            new_listens = response3.get('listens', 0)
            print(f"   New listens: {new_listens}")
            
            if new_listens == initial_listens + 1:
                print(f"   ✅ Listens incremented: {initial_listens} → {new_listens}")
            else:
                print(f"   ⚠️  Listens not incremented correctly: {initial_listens} → {new_listens}")
                self.failed_tests.append(f"Listen Analytics: Listens not incremented ({initial_listens} → {new_listens})")
        
        return success2 and success3

    def test_listen_analytics_invalid_slug(self):
        """Test POST /api/posts/nonexistent-slug/audio/listen returns 404"""
        print("\n" + "="*60)
        print("TESTING: Listen Analytics - Invalid Slug (404)")
        print("="*60)
        
        success, response, _ = self.run_test(
            "Track Listen (nonexistent slug)",
            "POST",
            "posts/nonexistent-slug-12345/audio/listen",
            404,
            headers={'Authorization': ''}
        )
        
        if success:
            print("   ✅ Returns 404 for nonexistent slug")
        
        return success

    def test_admin_stats_listens(self):
        """Test GET /api/admin/analytics/stats includes listens fields"""
        print("\n" + "="*60)
        print("TESTING: Admin Analytics Stats - Listens Fields")
        print("="*60)
        
        success, response, _ = self.run_test(
            "GET /api/admin/analytics/stats",
            "GET",
            "admin/analytics/stats",
            200
        )
        
        if success:
            listens = response.get('listens')
            listens_7d = response.get('listens_7d')
            top_posts = response.get('top_posts', [])
            
            print(f"   listens: {listens}")
            print(f"   listens_7d: {listens_7d}")
            print(f"   top_posts count: {len(top_posts)}")
            
            # Check listens field
            if listens is not None and isinstance(listens, int):
                print(f"   ✅ 'listens' field present (int): {listens}")
            else:
                print(f"   ❌ 'listens' field missing or wrong type: {listens}")
                self.failed_tests.append("Admin Stats: 'listens' field missing or wrong type")
            
            # Check listens_7d field
            if listens_7d is not None and isinstance(listens_7d, int):
                print(f"   ✅ 'listens_7d' field present (int): {listens_7d}")
            else:
                print(f"   ❌ 'listens_7d' field missing or wrong type: {listens_7d}")
                self.failed_tests.append("Admin Stats: 'listens_7d' field missing or wrong type")
            
            # Check top_posts entries have listens field
            if len(top_posts) > 0:
                print(f"\n   Checking top_posts entries for 'listens' field...")
                all_have_listens = True
                for i, post in enumerate(top_posts[:3]):  # Check first 3
                    post_listens = post.get('listens')
                    if post_listens is not None and isinstance(post_listens, int):
                        print(f"   ✅ top_posts[{i}] '{post.get('title', '')[:40]}': listens={post_listens}")
                    else:
                        print(f"   ❌ top_posts[{i}] missing 'listens' field")
                        all_have_listens = False
                        self.failed_tests.append(f"Admin Stats: top_posts[{i}] missing 'listens' field")
                
                if all_have_listens:
                    print("   ✅ All top_posts entries have 'listens' field")
            else:
                print("   ⚠️  No top_posts to check")
        
        return success

    def test_cached_audio_header(self):
        """Test GET /api/posts/{cached-slug}/audio?voice=male returns X-Audio-Cache: hit"""
        print("\n" + "="*60)
        print("TESTING: Cached Audio - X-Audio-Cache Header")
        print("="*60)
        print("⚠️  CRITICAL: Only testing the ONE cached slug to avoid burning ElevenLabs credits")
        
        # Use the cached slug from review request
        slug = "170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum"
        
        success, response, resp_obj = self.run_test(
            f"GET /api/posts/{slug}/audio?voice=male",
            "GET",
            f"posts/{slug}/audio?voice=male",
            200,
            headers={'Authorization': ''},
            check_headers={'X-Audio-Cache': 'hit'}
        )
        
        if success and resp_obj:
            cache_header = resp_obj.headers.get('X-Audio-Cache')
            if cache_header == 'hit':
                print(f"   ✅ X-Audio-Cache: hit (pre-generated cache)")
            else:
                print(f"   ⚠️  X-Audio-Cache: {cache_header} (expected 'hit')")
                self.failed_tests.append(f"Cached Audio: X-Audio-Cache is '{cache_header}', expected 'hit'")
        
        return success

    def test_regression_routes(self):
        """Test existing routes still work"""
        print("\n" + "="*60)
        print("TESTING: Regression - Existing Routes")
        print("="*60)
        
        tests = [
            ("GET /api/posts", "GET", "posts", 200, {}),
            ("GET /api/categories", "GET", "categories", 200, {}),
            ("GET /api/admin/posts", "GET", "admin/posts", 200, None),
            ("GET /api/posts/{real-slug}", "GET", "posts/the-ai-infrastructure-gold-rush-who-actually-wins", 200, {}),
        ]
        
        all_passed = True
        for name, method, endpoint, expected_status, headers in tests:
            if headers is None:
                # Admin route
                success, _, _ = self.run_test(name, method, endpoint, expected_status)
            else:
                # Public route
                success, _, _ = self.run_test(name, method, endpoint, expected_status, headers=headers or {'Authorization': ''})
            
            if not success:
                all_passed = False
        
        if all_passed:
            print("\n   ✅ All regression tests passed")
        
        return all_passed

def main():
    print("\n" + "="*60)
    print("TRADING NARRATIVE - LISTEN ANALYTICS TESTING")
    print("Session: Author Normalization + Listen Analytics + TTS Cache")
    print("="*60)
    
    tester = ListenAnalyticsTester()
    
    # Test 1: Admin Login
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    # Test 2: Author Normalization
    tester.test_author_normalization()
    
    # Test 3: Listen Analytics - Valid Slug
    tester.test_listen_analytics_valid_slug()
    
    # Test 4: Listen Analytics - Invalid Slug
    tester.test_listen_analytics_invalid_slug()
    
    # Test 5: Admin Stats - Listens Fields
    tester.test_admin_stats_listens()
    
    # Test 6: Cached Audio Header
    tester.test_cached_audio_header()
    
    # Test 7: Regression Tests
    tester.test_regression_routes()
    
    # Print results
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.failed_tests:
        print(f"\n❌ Failed tests ({len(tester.failed_tests)}):")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    else:
        print("\n✅ All tests passed!")
    
    print("="*60)
    
    return 0 if len(tester.failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
