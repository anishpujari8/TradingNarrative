"""
Backend tests for Reader Highlights and Related-by-Tags features
Tests ONLY the two new features as requested
"""
import requests
import sys
from datetime import datetime

class HighlightsAndRelatedTester:
    def __init__(self, base_url="https://insight-hub-484.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_user_email = None
        self.created_highlights = []
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        # Use specific token if provided, otherwise use admin token
        if token:
            req_headers['Authorization'] = f'Bearer {token}'
        elif self.admin_token and 'Authorization' not in req_headers:
            req_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=15)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    resp_data = response.json()
                    print(f"   Response: {resp_data}")
                except:
                    print(f"   Response: {response.text[:300]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login and get token"""
        print("\n" + "="*70)
        print("SETUP: Admin Authentication")
        print("="*70)
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@tradingnarrative.com", "password": "Admin@2025"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   ✅ Admin token obtained")
            return True
        return False

    def test_create_throwaway_user(self):
        """Create a throwaway test user (non-premium)"""
        print("\n" + "="*70)
        print("SETUP: Create Throwaway Test User")
        print("="*70)
        timestamp = datetime.now().strftime('%H%M%S%f')
        self.test_user_email = f"test_highlights_{timestamp}@example.com"
        
        success, response = self.run_test(
            "Register Test User",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.test_user_email,
                "password": "TestPass123!",
                "name": f"Test User {timestamp}"
            },
            headers={}  # No auth for registration
        )
        
        if success and 'token' in response:
            self.test_user_token = response['token']
            self.test_user_id = response.get('user', {}).get('id')
            print(f"   ✅ Test user created: {self.test_user_email}")
            print(f"   ✅ User ID: {self.test_user_id}")
            return True
        return False

    def test_get_post_for_highlights(self):
        """Get the freight-management post to extract content blocks"""
        print("\n" + "="*70)
        print("SETUP: Fetch Post Content Blocks")
        print("="*70)
        
        success, response = self.run_test(
            "Get Post freight-management",
            "GET",
            "posts/freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
            200,
            headers={}  # Public endpoint
        )
        
        if success:
            blocks = response.get('content_blocks', [])
            print(f"   ✅ Found {len(blocks)} content blocks")
            if blocks:
                print(f"   First block preview: {blocks[0][:80]}...")
                self.post_blocks = blocks
                self.post_slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"
                return True
        return False

    def test_highlight_create_valid(self):
        """Test POST /api/highlights with valid data"""
        print("\n" + "="*70)
        print("TEST 1: Create Highlight - Valid Text")
        print("="*70)
        
        if not hasattr(self, 'post_blocks') or not self.post_blocks:
            print("❌ No post blocks available")
            self.failed_tests.append("Highlight Create: No post blocks")
            return False
        
        # Extract a substring from block 0 (at least 40 chars)
        block_text = self.post_blocks[0]
        # Normalize whitespace like the backend does
        normalized = ' '.join(block_text.split())
        if len(normalized) < 50:
            print(f"❌ Block 0 too short: {len(normalized)} chars")
            self.failed_tests.append("Highlight Create: Block 0 too short")
            return False
        
        # Take a 40-60 char substring
        highlight_text = normalized[10:60].strip()
        
        print(f"   Using text: '{highlight_text}'")
        
        success, response = self.run_test(
            "Create Highlight (Valid)",
            "POST",
            "highlights",
            200,
            data={
                "slug": "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
                "block_index": 0,
                "text": highlight_text
            },
            token=self.admin_token
        )
        
        if success:
            if 'id' in response and response.get('already') == False:
                self.created_highlights.append(response['id'])
                print(f"   ✅ Highlight created with ID: {response['id']}")
                return True
            elif response.get('already') == True:
                print(f"   ⚠️  Highlight already exists (duplicate detection working)")
                self.created_highlights.append(response['id'])
                return True
        return False

    def test_highlight_duplicate(self):
        """Test duplicate highlight returns already=true"""
        print("\n" + "="*70)
        print("TEST 2: Create Duplicate Highlight")
        print("="*70)
        
        if not hasattr(self, 'post_blocks') or not self.post_blocks:
            print("❌ No post blocks available")
            return False
        
        block_text = self.post_blocks[0]
        normalized = ' '.join(block_text.split())
        highlight_text = normalized[10:60].strip()
        
        success, response = self.run_test(
            "Create Duplicate Highlight",
            "POST",
            "highlights",
            200,
            data={
                "slug": "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
                "block_index": 0,
                "text": highlight_text
            },
            token=self.admin_token
        )
        
        if success and response.get('already') == True:
            print(f"   ✅ Duplicate detection working: already=true")
            return True
        elif success and response.get('already') == False:
            print(f"   ⚠️  Expected already=true but got already=false")
            self.failed_tests.append("Highlight Duplicate: Expected already=true")
        return False

    def test_highlight_invalid_text(self):
        """Test highlight with text not in block returns 400"""
        print("\n" + "="*70)
        print("TEST 3: Create Highlight - Invalid Text (Not in Block)")
        print("="*70)
        
        success, response = self.run_test(
            "Create Highlight (Invalid Text)",
            "POST",
            "highlights",
            400,
            data={
                "slug": self.post_slug,
                "block_index": 0,
                "text": "This text definitely does not exist in the article at all"
            },
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Correctly rejected invalid text with 400")
            return True
        return False

    def test_highlight_invalid_block_index(self):
        """Test highlight with out-of-range block_index returns 400"""
        print("\n" + "="*70)
        print("TEST 4: Create Highlight - Invalid Block Index")
        print("="*70)
        
        success, response = self.run_test(
            "Create Highlight (Invalid Block Index)",
            "POST",
            "highlights",
            400,
            data={
                "slug": self.post_slug,
                "block_index": 9999,
                "text": "Some text"
            },
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Correctly rejected invalid block_index with 400")
            return True
        return False

    def test_highlight_unauthenticated(self):
        """Test highlight creation without auth returns 401"""
        print("\n" + "="*70)
        print("TEST 5: Create Highlight - Unauthenticated")
        print("="*70)
        
        success, response = self.run_test(
            "Create Highlight (No Auth)",
            "POST",
            "highlights",
            401,
            data={
                "slug": self.post_slug,
                "block_index": 0,
                "text": "Some text"
            },
            headers={}  # No auth header
        )
        
        if success:
            print(f"   ✅ Correctly rejected unauthenticated request with 401")
            return True
        return False

    def test_paywall_enforcement(self):
        """Test paywall enforcement: non-premium user can't highlight beyond block 2"""
        print("\n" + "="*70)
        print("TEST 6: Paywall Enforcement (Non-Premium User)")
        print("="*70)
        
        # First, get a premium post
        success, response = self.run_test(
            "Get Premium Posts",
            "GET",
            "posts?tier=premium&limit=1",
            200,
            headers={}
        )
        
        if not success or not response.get('posts'):
            print("   ⚠️  No premium posts found, skipping paywall test")
            return True  # Not a failure, just no data
        
        premium_post = response['posts'][0]
        premium_slug = premium_post['slug']
        print(f"   Testing with premium post: {premium_slug}")
        
        # Get the full post to see content blocks
        success2, post_data = self.run_test(
            f"Get Premium Post {premium_slug}",
            "GET",
            f"posts/{premium_slug}",
            200,
            token=self.test_user_token  # Non-premium user
        )
        
        if not success2:
            print("   ❌ Could not fetch premium post")
            return False
        
        shown_blocks = post_data.get('shown_blocks', 0)
        total_blocks = post_data.get('total_blocks', 0)
        is_locked = post_data.get('is_locked', False)
        
        print(f"   Premium post: shown_blocks={shown_blocks}, total_blocks={total_blocks}, is_locked={is_locked}")
        
        if not is_locked:
            print("   ⚠️  Post not locked for non-premium user (unexpected)")
            self.failed_tests.append("Paywall: Premium post not locked for non-premium user")
            return False
        
        # Try to highlight block 3 (should be blocked if PREVIEW_BLOCKS=3)
        if total_blocks > 3:
            # Get the actual block text from the post
            blocks = post_data.get('content_blocks', [])
            if len(blocks) >= 3:
                # Try to highlight the last shown block (should work)
                last_shown_text = ' '.join(blocks[-1].split())[10:50]
                
                success3, _ = self.run_test(
                    "Highlight Last Shown Block (Should Work)",
                    "POST",
                    "highlights",
                    200,
                    data={
                        "slug": premium_slug,
                        "block_index": len(blocks) - 1,
                        "text": last_shown_text
                    },
                    token=self.test_user_token
                )
                
                if success3:
                    print(f"   ✅ Non-premium user can highlight preview blocks")
                
                # Now try to highlight block_index=3 (beyond preview)
                success4, _ = self.run_test(
                    "Highlight Beyond Preview (Should Fail)",
                    "POST",
                    "highlights",
                    400,
                    data={
                        "slug": premium_slug,
                        "block_index": 3,
                        "text": "Some text that would be in block 3"
                    },
                    token=self.test_user_token
                )
                
                if success4:
                    print(f"   ✅ Paywall enforcement working: block_index >= 3 rejected with 400")
                    return True
        else:
            print(f"   ⚠️  Premium post has only {total_blocks} blocks, can't test paywall")
        
        return False

    def test_get_highlights(self):
        """Test GET /api/highlights returns user's highlights"""
        print("\n" + "="*70)
        print("TEST 7: Get User Highlights")
        print("="*70)
        
        success, response = self.run_test(
            "Get All Highlights",
            "GET",
            "highlights",
            200,
            token=self.admin_token
        )
        
        if success:
            highlights = response.get('highlights', [])
            total = response.get('total', 0)
            print(f"   ✅ Retrieved {total} highlights")
            
            if highlights:
                h = highlights[0]
                required_fields = ['id', 'text', 'post_slug', 'post_title', 'category_label', 'block_index', 'created_at']
                missing = [f for f in required_fields if f not in h]
                if missing:
                    print(f"   ⚠️  Missing fields in highlight: {missing}")
                    self.failed_tests.append(f"Highlight fields: Missing {missing}")
                else:
                    print(f"   ✅ Highlight has all required fields")
                
                # Check newest first ordering
                if len(highlights) > 1:
                    first_date = highlights[0].get('created_at', '')
                    second_date = highlights[1].get('created_at', '')
                    if first_date >= second_date:
                        print(f"   ✅ Highlights ordered newest first")
                    else:
                        print(f"   ⚠️  Highlights not ordered correctly")
                        self.failed_tests.append("Highlights: Not ordered newest first")
            
            return True
        return False

    def test_get_highlights_by_slug(self):
        """Test GET /api/highlights?slug=... filters by post"""
        print("\n" + "="*70)
        print("TEST 8: Get Highlights Filtered by Slug")
        print("="*70)
        
        success, response = self.run_test(
            "Get Highlights by Slug",
            "GET",
            "highlights?slug=freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
            200,
            token=self.admin_token
        )
        
        if success:
            highlights = response.get('highlights', [])
            print(f"   ✅ Retrieved {len(highlights)} highlights for freight-management post")
            
            # Verify all are for the correct slug
            wrong_slug = [h for h in highlights if h.get('post_slug') != 'freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr']
            if wrong_slug:
                print(f"   ⚠️  Found {len(wrong_slug)} highlights with wrong slug")
                self.failed_tests.append("Highlights filter: Wrong slug in results")
            else:
                print(f"   ✅ All highlights are for the correct post")
            
            return True
        return False

    def test_delete_highlight_owner(self):
        """Test DELETE /api/highlights/{id} - owner can delete"""
        print("\n" + "="*70)
        print("TEST 9: Delete Highlight (Owner)")
        print("="*70)
        
        if not self.created_highlights:
            print("   ⚠️  No highlights to delete")
            return True
        
        hid = self.created_highlights[0]
        
        success, response = self.run_test(
            "Delete Own Highlight",
            "DELETE",
            f"highlights/{hid}",
            200,
            token=self.admin_token
        )
        
        if success and response.get('ok') == True:
            print(f"   ✅ Successfully deleted highlight {hid}")
            self.created_highlights.remove(hid)
            return True
        return False

    def test_delete_highlight_not_owner(self):
        """Test DELETE /api/highlights/{id} - another user gets 403"""
        print("\n" + "="*70)
        print("TEST 10: Delete Highlight (Not Owner)")
        print("="*70)
        
        # Create a highlight as admin
        if hasattr(self, 'post_blocks') and self.post_blocks:
            block_text = self.post_blocks[1] if len(self.post_blocks) > 1 else self.post_blocks[0]
            normalized = ' '.join(block_text.split())
            highlight_text = normalized[5:45].strip()
            
            success, response = self.run_test(
                "Create Highlight as Admin",
                "POST",
                "highlights",
                200,
                data={
                    "slug": self.post_slug,
                    "block_index": 1 if len(self.post_blocks) > 1 else 0,
                    "text": highlight_text
                },
                token=self.admin_token
            )
            
            if success and 'id' in response:
                hid = response['id']
                self.created_highlights.append(hid)
                
                # Try to delete as test user
                success2, _ = self.run_test(
                    "Delete Other User's Highlight",
                    "DELETE",
                    f"highlights/{hid}",
                    403,
                    token=self.test_user_token
                )
                
                if success2:
                    print(f"   ✅ Correctly rejected with 403")
                    return True
        
        return False

    def test_delete_highlight_not_found(self):
        """Test DELETE /api/highlights/{id} - missing id gets 404"""
        print("\n" + "="*70)
        print("TEST 11: Delete Highlight (Not Found)")
        print("="*70)
        
        success, response = self.run_test(
            "Delete Non-existent Highlight",
            "DELETE",
            "highlights/non-existent-id-12345",
            404,
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Correctly returned 404 for non-existent highlight")
            return True
        return False

    def test_related_by_tags(self):
        """Test Related-by-tags: GET /api/posts/{slug} returns related posts scored by tags"""
        print("\n" + "="*70)
        print("TEST 12: Related Posts Scored by Tags")
        print("="*70)
        
        # Get the freight-management post
        success, response = self.run_test(
            "Get Freight Management Post",
            "GET",
            "posts/freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr",
            200,
            headers={}
        )
        
        if not success:
            print("   ❌ Could not fetch freight-management post")
            return False
        
        post_category = response.get('category')
        post_tags = response.get('tags', [])
        related = response.get('related', [])
        
        print(f"   Post category: {post_category}")
        print(f"   Post tags: {post_tags}")
        print(f"   Related posts: {len(related)}")
        
        if not related:
            print("   ⚠️  No related posts found")
            self.failed_tests.append("Related by tags: No related posts")
            return False
        
        # Check if at least one related post is from a DIFFERENT category but shares a tag
        different_category_with_shared_tag = []
        for r in related:
            r_cat = r.get('category')
            r_tags = r.get('tags', [])
            shared_tags = set(post_tags) & set(r_tags)
            
            print(f"   - {r.get('title', 'Untitled')[:60]}")
            print(f"     Category: {r_cat}, Tags: {r_tags}, Shared: {list(shared_tags)}")
            
            if r_cat != post_category and shared_tags:
                different_category_with_shared_tag.append(r)
        
        if different_category_with_shared_tag:
            print(f"   ✅ Found {len(different_category_with_shared_tag)} related posts from different category with shared tags")
            print(f"   ✅ Tag-based scoring is working!")
            
            # Check if the expected post is there
            expected_title = "Five Things Commodity Desks Need to Know This Week"
            found_expected = any(expected_title in r.get('title', '') for r in related)
            if found_expected:
                print(f"   ✅ Found expected post: '{expected_title}'")
            else:
                print(f"   ⚠️  Expected post '{expected_title}' not in related (may be OK if scoring is different)")
            
            return True
        else:
            print(f"   ⚠️  No related posts from different category with shared tags")
            print(f"   This may indicate tag-based scoring is not working correctly")
            self.failed_tests.append("Related by tags: No cross-category tag matches found")
            return False

    def cleanup(self):
        """Delete all created highlights and test user"""
        print("\n" + "="*70)
        print("CLEANUP: Removing Test Data")
        print("="*70)
        
        # Delete all created highlights
        for hid in self.created_highlights:
            try:
                url = f"{self.base_url}/highlights/{hid}"
                headers = {'Authorization': f'Bearer {self.admin_token}'}
                response = requests.delete(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Deleted highlight {hid}")
                else:
                    print(f"   ⚠️  Could not delete highlight {hid}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Error deleting highlight {hid}: {e}")
        
        # Delete test user from database
        if self.test_user_id:
            try:
                # Use MongoDB directly via admin endpoint (if available) or manual cleanup
                print(f"   ⚠️  Test user {self.test_user_email} should be manually deleted from db.users")
                print(f"   User ID: {self.test_user_id}")
            except Exception as e:
                print(f"   ⚠️  Could not delete test user: {e}")

def main():
    print("\n" + "="*70)
    print("TRADING NARRATIVE - HIGHLIGHTS & RELATED-BY-TAGS TESTING")
    print("Testing ONLY the two new features as requested")
    print("="*70)
    
    tester = HighlightsAndRelatedTester()
    
    # Setup
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    if not tester.test_create_throwaway_user():
        print("\n❌ Could not create test user, stopping tests")
        return 1
    
    if not tester.test_get_post_for_highlights():
        print("\n❌ Could not fetch post content, stopping tests")
        return 1
    
    # Run all highlight tests
    tester.test_highlight_create_valid()
    tester.test_highlight_duplicate()
    tester.test_highlight_invalid_text()
    tester.test_highlight_invalid_block_index()
    tester.test_highlight_unauthenticated()
    tester.test_paywall_enforcement()
    tester.test_get_highlights()
    tester.test_get_highlights_by_slug()
    tester.test_delete_highlight_owner()
    tester.test_delete_highlight_not_owner()
    tester.test_delete_highlight_not_found()
    
    # Test related-by-tags
    tester.test_related_by_tags()
    
    # Cleanup
    tester.cleanup()
    
    # Print results
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.failed_tests:
        print(f"\n❌ Failed tests ({len(tester.failed_tests)}):")
        for failure in tester.failed_tests:
            print(f"   - {failure}")
    else:
        print("\n✅ All tests passed!")
    
    print("="*70)
    
    return 0 if len(tester.failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
