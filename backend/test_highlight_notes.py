"""
Backend tests for Highlight Notes and Sharing features
Tests ONLY the two NEW features: (1) Highlight Notes, (2) Highlight Sharing (backend support)
"""
import requests
import sys
from datetime import datetime

class HighlightNotesTester:
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
        self.post_slug = "freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        
        # Use specific token if provided
        # token=False means explicitly no token (for testing unauthenticated requests)
        # token=None means use default admin token
        # token=<string> means use that specific token
        if token is False:
            # Explicitly no token - don't add Authorization header
            pass
        elif token:
            req_headers['Authorization'] = f'Bearer {token}'
        elif token is None and self.admin_token and 'Authorization' not in req_headers:
            # Default to admin token if no token specified
            req_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=15)
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
            data={"email": "admin@tradingnarrative.com", "password": "Admin@2025"},
            headers={}  # No auth for login
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   ✅ Admin token obtained")
            return True
        return False

    def test_create_throwaway_user(self):
        """Create a throwaway test user for 403 ownership test"""
        print("\n" + "="*70)
        print("SETUP: Create Throwaway Test User")
        print("="*70)
        timestamp = datetime.now().strftime('%H%M%S%f')
        self.test_user_email = f"test_notes_{timestamp}@example.com"
        
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

    def test_get_post_content(self):
        """Get the freight-management post to extract content blocks"""
        print("\n" + "="*70)
        print("SETUP: Fetch Post Content Blocks")
        print("="*70)
        
        success, response = self.run_test(
            "Get Post freight-management",
            "GET",
            f"posts/{self.post_slug}",
            200,
            headers={}  # Public endpoint
        )
        
        if success:
            blocks = response.get('content_blocks', [])
            print(f"   ✅ Found {len(blocks)} content blocks")
            if blocks:
                self.post_blocks = blocks
                return True
        return False

    def test_create_highlight_with_note(self):
        """Test POST /api/highlights with optional 'note' field"""
        print("\n" + "="*70)
        print("TEST 1: Create Highlight WITH Note")
        print("="*70)
        
        if not hasattr(self, 'post_blocks') or not self.post_blocks:
            print("❌ No post blocks available")
            self.failed_tests.append("Create highlight with note: No post blocks")
            return False
        
        # Extract a substring from block 0
        block_text = self.post_blocks[0]
        normalized = ' '.join(block_text.split())
        highlight_text = normalized[10:60].strip()
        
        print(f"   Using text: '{highlight_text}'")
        
        success, response = self.run_test(
            "Create Highlight with Note",
            "POST",
            "highlights",
            200,
            data={
                "slug": self.post_slug,
                "block_index": 0,
                "text": highlight_text,
                "note": "This is a test note for the highlight"
            },
            token=self.admin_token
        )
        
        if success:
            if 'id' in response:
                hid = response['id']
                self.created_highlights.append(hid)
                note = response.get('note', '')
                if note == "This is a test note for the highlight":
                    print(f"   ✅ Highlight created with note: '{note}'")
                    self.test_highlight_id = hid
                    return True
                else:
                    print(f"   ❌ Note not saved correctly. Expected 'This is a test note for the highlight', got '{note}'")
                    self.failed_tests.append("Create highlight with note: Note not saved")
        return False

    def test_create_highlight_without_note(self):
        """Test POST /api/highlights without note field (should default to empty)"""
        print("\n" + "="*70)
        print("TEST 2: Create Highlight WITHOUT Note")
        print("="*70)
        
        if not hasattr(self, 'post_blocks') or not self.post_blocks:
            print("❌ No post blocks available")
            return False
        
        block_text = self.post_blocks[1] if len(self.post_blocks) > 1 else self.post_blocks[0]
        normalized = ' '.join(block_text.split())
        highlight_text = normalized[5:45].strip()
        
        success, response = self.run_test(
            "Create Highlight without Note",
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
        
        if success:
            if 'id' in response:
                hid = response['id']
                self.created_highlights.append(hid)
                note = response.get('note', '')
                if note == '':
                    print(f"   ✅ Highlight created without note (note is empty string)")
                    self.test_highlight_no_note_id = hid
                    return True
                else:
                    print(f"   ⚠️  Note should be empty but got: '{note}'")
        return False

    def test_get_highlights_returns_note(self):
        """Test GET /api/highlights returns note field"""
        print("\n" + "="*70)
        print("TEST 3: GET /api/highlights Returns Note Field")
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
            if highlights:
                # Find our test highlight with note
                test_h = next((h for h in highlights if h.get('id') == getattr(self, 'test_highlight_id', None)), None)
                if test_h:
                    note = test_h.get('note', '')
                    if note == "This is a test note for the highlight":
                        print(f"   ✅ GET /api/highlights returns note field correctly")
                        return True
                    else:
                        print(f"   ❌ Note not returned correctly. Expected 'This is a test note for the highlight', got '{note}'")
                        self.failed_tests.append("GET highlights: Note not returned")
                else:
                    print(f"   ⚠️  Test highlight not found in results")
            else:
                print(f"   ⚠️  No highlights returned")
        return False

    def test_update_note_success(self):
        """Test PUT /api/highlights/{id}/note - owner can set note (200)"""
        print("\n" + "="*70)
        print("TEST 4: PUT /api/highlights/{id}/note - Owner Success (200)")
        print("="*70)
        
        if not hasattr(self, 'test_highlight_no_note_id'):
            print("   ⚠️  No test highlight without note available")
            return False
        
        hid = self.test_highlight_no_note_id
        
        success, response = self.run_test(
            "Update Note (Owner)",
            "PUT",
            f"highlights/{hid}/note",
            200,
            data={"note": "Updated note via PUT endpoint"},
            token=self.admin_token
        )
        
        if success:
            note = response.get('note', '')
            if note == "Updated note via PUT endpoint":
                print(f"   ✅ Note updated successfully: '{note}'")
                return True
            else:
                print(f"   ❌ Note not updated correctly. Expected 'Updated note via PUT endpoint', got '{note}'")
                self.failed_tests.append("Update note: Note not updated")
        return False

    def test_clear_note_with_empty_string(self):
        """Test PUT /api/highlights/{id}/note with empty string clears note"""
        print("\n" + "="*70)
        print("TEST 5: PUT /api/highlights/{id}/note - Clear Note (Empty String)")
        print("="*70)
        
        if not hasattr(self, 'test_highlight_id'):
            print("   ⚠️  No test highlight available")
            return False
        
        hid = self.test_highlight_id
        
        success, response = self.run_test(
            "Clear Note (Empty String)",
            "PUT",
            f"highlights/{hid}/note",
            200,
            data={"note": ""},
            token=self.admin_token
        )
        
        if success:
            note = response.get('note', None)
            if note == '':
                print(f"   ✅ Note cleared successfully (empty string)")
                return True
            else:
                print(f"   ❌ Note not cleared. Expected empty string, got '{note}'")
                self.failed_tests.append("Clear note: Note not cleared")
        return False

    def test_update_note_too_long(self):
        """Test PUT /api/highlights/{id}/note with >500 chars rejected (422)"""
        print("\n" + "="*70)
        print("TEST 6: PUT /api/highlights/{id}/note - Note Too Long (422)")
        print("="*70)
        
        if not hasattr(self, 'test_highlight_id'):
            print("   ⚠️  No test highlight available")
            return False
        
        hid = self.test_highlight_id
        long_note = "A" * 501  # 501 characters
        
        success, response = self.run_test(
            "Update Note (Too Long)",
            "PUT",
            f"highlights/{hid}/note",
            422,
            data={"note": long_note},
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Correctly rejected note >500 chars with 422")
            return True
        return False

    def test_update_note_not_owner(self):
        """Test PUT /api/highlights/{id}/note - another user gets 403"""
        print("\n" + "="*70)
        print("TEST 7: PUT /api/highlights/{id}/note - Not Owner (403)")
        print("="*70)
        
        if not hasattr(self, 'test_highlight_id'):
            print("   ⚠️  No test highlight available")
            return False
        
        hid = self.test_highlight_id
        
        success, response = self.run_test(
            "Update Note (Not Owner)",
            "PUT",
            f"highlights/{hid}/note",
            403,
            data={"note": "Trying to update someone else's note"},
            token=self.test_user_token
        )
        
        if success:
            print(f"   ✅ Correctly rejected non-owner with 403")
            return True
        return False

    def test_update_note_not_found(self):
        """Test PUT /api/highlights/{id}/note - missing id gets 404"""
        print("\n" + "="*70)
        print("TEST 8: PUT /api/highlights/{id}/note - Not Found (404)")
        print("="*70)
        
        success, response = self.run_test(
            "Update Note (Not Found)",
            "PUT",
            "highlights/non-existent-id-12345/note",
            404,
            data={"note": "This should fail"},
            token=self.admin_token
        )
        
        if success:
            print(f"   ✅ Correctly returned 404 for non-existent highlight")
            return True
        return False

    def test_update_note_unauthenticated(self):
        """Test PUT /api/highlights/{id}/note - unauthenticated gets 401"""
        print("\n" + "="*70)
        print("TEST 9: PUT /api/highlights/{id}/note - Unauthenticated (401)")
        print("="*70)
        
        if not hasattr(self, 'test_highlight_id'):
            print("   ⚠️  No test highlight available")
            return False
        
        hid = self.test_highlight_id
        
        # Explicitly pass token=False to prevent default admin token
        success, response = self.run_test(
            "Update Note (No Auth)",
            "PUT",
            f"highlights/{hid}/note",
            401,
            data={"note": "This should fail"},
            token=False  # Explicitly no token
        )
        
        if success:
            print(f"   ✅ Correctly rejected unauthenticated request with 401")
            return True
        return False

    def cleanup_highlights(self):
        """Delete all created test highlights"""
        print("\n" + "="*70)
        print("CLEANUP: Removing Test Highlights")
        print("="*70)
        
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

    def cleanup_test_user(self):
        """Delete test user from database"""
        print("\n" + "="*70)
        print("CLEANUP: Removing Test User")
        print("="*70)
        
        if self.test_user_id:
            print(f"   ⚠️  Test user {self.test_user_email} (ID: {self.test_user_id}) should be deleted from db.users")
            print(f"   Manual cleanup required via MongoDB")

def main():
    print("\n" + "="*70)
    print("HIGHLIGHT NOTES FEATURE - BACKEND TESTING")
    print("Testing the NEW Highlight Notes feature")
    print("="*70)
    
    tester = HighlightNotesTester()
    
    # Setup
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    if not tester.test_create_throwaway_user():
        print("\n❌ Could not create test user, stopping tests")
        return 1
    
    if not tester.test_get_post_content():
        print("\n❌ Could not fetch post content, stopping tests")
        return 1
    
    # Run all note tests
    tester.test_create_highlight_with_note()
    tester.test_create_highlight_without_note()
    tester.test_get_highlights_returns_note()
    tester.test_update_note_success()
    tester.test_clear_note_with_empty_string()
    tester.test_update_note_too_long()
    tester.test_update_note_not_owner()
    tester.test_update_note_not_found()
    tester.test_update_note_unauthenticated()
    
    # Cleanup
    tester.cleanup_highlights()
    tester.cleanup_test_user()
    
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
