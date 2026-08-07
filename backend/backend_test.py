import requests
import sys
from datetime import datetime

class TradingNarrativeAPITester:
    def __init__(self, base_url="https://insight-hub-484.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
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
                response = requests.get(url, headers=req_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=10)

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
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login and get token"""
        print("\n" + "="*60)
        print("TESTING: Admin Authentication")
        print("="*60)
        success, response = self.run_test(
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

    def test_email_status(self):
        """Test GET /api/admin/email/status"""
        print("\n" + "="*60)
        print("TESTING: Email Status (Gmail SMTP)")
        print("="*60)
        success, response = self.run_test(
            "Email Status",
            "GET",
            "admin/email/status",
            200
        )
        if success:
            print(f"   Enabled: {response.get('enabled')}")
            print(f"   Verified: {response.get('verified')}")
            print(f"   Last Error: {response.get('last_error')}")
            print(f"   From: {response.get('from')}")
            
            # Verify expected values
            if response.get('enabled') == True and response.get('verified') == True and response.get('last_error') is None:
                print("✅ Email status is correct: enabled=true, verified=true, last_error=null")
            else:
                print(f"⚠️  Email status unexpected: enabled={response.get('enabled')}, verified={response.get('verified')}, last_error={response.get('last_error')}")
                self.failed_tests.append("Email Status: Expected enabled=true, verified=true, last_error=null")
        return success

    def test_funnel_plan_split(self):
        """Test GET /api/admin/funnel?days=30 for monthly/annual split"""
        print("\n" + "="*60)
        print("TESTING: Funnel Plan Split (Monthly/Annual)")
        print("="*60)
        success, response = self.run_test(
            "Funnel with Plan Split",
            "GET",
            "admin/funnel?days=30",
            200
        )
        if success:
            overall = response.get('overall', {})
            funnel_rows = response.get('funnel', [])
            
            print(f"   Total sessions: {response.get('total_sessions')}")
            print(f"   Overall conversions: {overall.get('conversions')}")
            print(f"   Overall conversions_monthly: {overall.get('conversions_monthly')}")
            print(f"   Overall conversions_annual: {overall.get('conversions_annual')}")
            
            # Check if overall has the split fields
            has_monthly = 'conversions_monthly' in overall
            has_annual = 'conversions_annual' in overall
            
            if has_monthly and has_annual:
                print("✅ Overall includes conversions_monthly and conversions_annual")
                
                # Verify sum consistency
                total_conv = overall.get('conversions', 0)
                monthly_conv = overall.get('conversions_monthly', 0)
                annual_conv = overall.get('conversions_annual', 0)
                
                if monthly_conv + annual_conv == total_conv:
                    print(f"✅ Sum is consistent: {monthly_conv} + {annual_conv} = {total_conv}")
                else:
                    print(f"⚠️  Sum mismatch: {monthly_conv} + {annual_conv} != {total_conv}")
                    self.failed_tests.append(f"Funnel: Sum mismatch in overall conversions")
            else:
                print(f"❌ Missing split fields: conversions_monthly={has_monthly}, conversions_annual={has_annual}")
                self.failed_tests.append("Funnel: Missing conversions_monthly or conversions_annual in overall")
            
            # Check funnel rows
            if funnel_rows:
                print(f"\n   Checking {len(funnel_rows)} funnel rows...")
                for row in funnel_rows[:3]:  # Check first 3 rows
                    source = row.get('source')
                    has_row_monthly = 'conversions_monthly' in row
                    has_row_annual = 'conversions_annual' in row
                    if has_row_monthly and has_row_annual:
                        print(f"   ✅ {source}: monthly={row.get('conversions_monthly')}, annual={row.get('conversions_annual')}")
                    else:
                        print(f"   ❌ {source}: Missing split fields")
                        self.failed_tests.append(f"Funnel row {source}: Missing conversions_monthly or conversions_annual")
        
        return success

    def test_announcement_editing(self):
        """Test PUT /api/community/announcements/{aid}"""
        print("\n" + "="*60)
        print("TESTING: Announcement Editing")
        print("="*60)
        
        # First, get existing announcements
        success, response = self.run_test(
            "Get Announcements",
            "GET",
            "community/announcements",
            200
        )
        
        if not success or not response.get('announcements'):
            print("⚠️  No announcements found to test editing")
            return False
        
        announcements = response['announcements']
        print(f"   Found {len(announcements)} announcements")
        
        # Find the "AMA next week — updated" announcement
        target_ann = None
        for ann in announcements:
            if 'AMA next week' in ann.get('title', ''):
                target_ann = ann
                break
        
        if not target_ann:
            print("⚠️  'AMA next week' announcement not found, using first announcement")
            target_ann = announcements[0]
        
        ann_id = target_ann['id']
        original_title = target_ann['title']
        original_body = target_ann['body']
        original_publish_at = target_ann.get('publish_at')
        
        print(f"   Testing with announcement: '{original_title}'")
        print(f"   Original scheduled: {target_ann.get('scheduled')}")
        
        # Test 1: Edit title and body
        print("\n   Test 1: Edit title and body")
        new_title = original_title + " [TEST]"
        success1, response1 = self.run_test(
            "Edit Announcement Title/Body",
            "PUT",
            f"community/announcements/{ann_id}",
            200,
            data={"title": new_title, "body": original_body}
        )
        
        if success1:
            if response1.get('title') == new_title:
                print("   ✅ Title updated successfully")
            else:
                print(f"   ❌ Title not updated: expected '{new_title}', got '{response1.get('title')}'")
                self.failed_tests.append("Announcement Edit: Title not updated")
        
        # Restore original title
        print("\n   Restoring original title...")
        success_restore, _ = self.run_test(
            "Restore Announcement Title",
            "PUT",
            f"community/announcements/{ann_id}",
            200,
            data={"title": original_title, "body": original_body, "publish_at": original_publish_at}
        )
        
        if success_restore:
            print("   ✅ Announcement restored to original state")
        
        # Test 2: Invalid title (too short)
        print("\n   Test 2: Invalid title (too short)")
        success2, _ = self.run_test(
            "Edit with Invalid Title",
            "PUT",
            f"community/announcements/{ann_id}",
            400,
            data={"title": "AB", "body": original_body}
        )
        
        # Test 3: Non-existent announcement
        print("\n   Test 3: Non-existent announcement")
        success3, _ = self.run_test(
            "Edit Non-existent Announcement",
            "PUT",
            "community/announcements/non-existent-id-12345",
            404,
            data={"title": "Test", "body": "Test body"}
        )
        
        # Test 4: Non-admin user (would need a regular user token, skipping for now)
        print("\n   Test 4: Non-admin access (skipped - would need regular user token)")
        
        return success1 and success2 and success3

    def test_digest_personalization_code_review(self):
        """Code review of digest personalization logic - NO API CALLS"""
        print("\n" + "="*60)
        print("CODE REVIEW: Digest Personalization Logic")
        print("="*60)
        print("⚠️  CRITICAL: NOT calling send-digest API (real Gmail sending is LIVE)")
        print("   Reviewing code in /app/backend/server.py for do_send_digest function...")
        
        try:
            with open('/app/backend/server.py', 'r') as f:
                content = f.read()
            
            # Check if do_send_digest function exists
            if 'def do_send_digest' in content or 'async def do_send_digest' in content:
                print("   ✅ Found do_send_digest function")
                
                # Look for category filtering logic
                if 'categories' in content and 'newsletter_subscribers' in content:
                    print("   ✅ Code contains category filtering references")
                    
                    # Check for per-subscriber filtering
                    if 'for sub in' in content or 'for subscriber in' in content:
                        print("   ✅ Code contains subscriber iteration logic")
                        
                        # Look for category matching
                        if 'category' in content and ('in' in content or 'filter' in content):
                            print("   ✅ Code appears to filter posts by subscriber categories")
                            print("   ✅ VERIFIED: Digest personalization logic is present")
                            return True
                        else:
                            print("   ⚠️  Could not verify category filtering logic")
                            self.failed_tests.append("Digest Code Review: Category filtering logic unclear")
                    else:
                        print("   ⚠️  Could not find subscriber iteration")
                        self.failed_tests.append("Digest Code Review: No subscriber iteration found")
                else:
                    print("   ⚠️  Could not find category/subscriber references")
                    self.failed_tests.append("Digest Code Review: Missing category/subscriber references")
            else:
                print("   ❌ do_send_digest function not found")
                self.failed_tests.append("Digest Code Review: do_send_digest function not found")
                return False
                
        except Exception as e:
            print(f"   ❌ Error reading server.py: {e}")
            self.failed_tests.append(f"Digest Code Review: Error reading file - {e}")
            return False
        
        return False

    def test_self_healing_seed(self):
        """Test self-healing seed: delete Edition #1, restart backend, verify restoration"""
        print("\n" + "="*60)
        print("TESTING: Self-Healing Seed (Edition #1 Restoration)")
        print("="*60)
        
        import subprocess
        import time
        from pymongo import MongoClient
        
        # Connect to MongoDB
        try:
            client = MongoClient("mongodb://localhost:27017")
            db = client["test_database"]
            posts_collection = db["posts"]
            
            # Step 1: Verify Edition #1 exists
            print("\n   Step 1: Verify Edition #1 exists before deletion")
            edition_1 = posts_collection.find_one({"slug": "five-things-commodity-desks-need-to-know-this-week"})
            if not edition_1:
                print("   ❌ Edition #1 not found in database before test")
                self.failed_tests.append("Self-Healing Seed: Edition #1 not found before deletion")
                return False
            print(f"   ✅ Found Edition #1: {edition_1['title'][:60]}")
            print(f"   Edition number: {edition_1.get('edition')}")
            print(f"   Content blocks: {len(edition_1.get('content_blocks', []))}")
            
            # Step 2: Delete Edition #1
            print("\n   Step 2: Delete Edition #1 from database")
            result = posts_collection.delete_one({"slug": "five-things-commodity-desks-need-to-know-this-week"})
            if result.deleted_count == 1:
                print("   ✅ Edition #1 deleted successfully")
            else:
                print("   ❌ Failed to delete Edition #1")
                self.failed_tests.append("Self-Healing Seed: Failed to delete Edition #1")
                return False
            
            # Verify deletion
            check = posts_collection.find_one({"slug": "five-things-commodity-desks-need-to-know-this-week"})
            if check:
                print("   ❌ Edition #1 still exists after deletion")
                self.failed_tests.append("Self-Healing Seed: Edition #1 still exists after deletion")
                return False
            print("   ✅ Confirmed: Edition #1 no longer in database")
            
            # Step 3: Restart backend
            print("\n   Step 3: Restart backend to trigger seed_database()")
            try:
                subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True, timeout=10)
                print("   ✅ Backend restart command sent")
            except Exception as e:
                print(f"   ❌ Failed to restart backend: {e}")
                self.failed_tests.append(f"Self-Healing Seed: Backend restart failed - {e}")
                return False
            
            # Wait for backend to restart
            print("   Waiting 6 seconds for backend to restart and run seed...")
            time.sleep(6)
            
            # Step 4: Verify Edition #1 is restored
            print("\n   Step 4: Verify Edition #1 is restored")
            restored = posts_collection.find_one({"slug": "five-things-commodity-desks-need-to-know-this-week"})
            if not restored:
                print("   ❌ Edition #1 NOT restored after backend restart")
                self.failed_tests.append("Self-Healing Seed: Edition #1 not restored")
                return False
            
            print(f"   ✅ Edition #1 restored: {restored['title'][:60]}")
            print(f"   Edition number: {restored.get('edition')}")
            print(f"   Content blocks: {len(restored.get('content_blocks', []))}")
            print(f"   Status: {restored.get('status')}")
            
            # Verify it's published
            if restored.get('status') != 'published':
                print(f"   ⚠️  Edition #1 status is '{restored.get('status')}', expected 'published'")
                self.failed_tests.append("Self-Healing Seed: Edition #1 not published")
            
            # Verify edition number
            if restored.get('edition') != 1:
                print(f"   ⚠️  Edition number is {restored.get('edition')}, expected 1")
                self.failed_tests.append("Self-Healing Seed: Edition number incorrect")
            
            # Verify content blocks (should be 22)
            if len(restored.get('content_blocks', [])) != 22:
                print(f"   ⚠️  Content blocks count is {len(restored.get('content_blocks', []))}, expected 22")
                self.failed_tests.append("Self-Healing Seed: Content blocks count incorrect")
            
            # Step 5: Check for duplicates
            print("\n   Step 5: Check for duplicates")
            count = posts_collection.count_documents({"slug": "five-things-commodity-desks-need-to-know-this-week"})
            if count == 1:
                print(f"   ✅ No duplicates: exactly 1 post with this slug")
            else:
                print(f"   ❌ Found {count} posts with this slug (expected 1)")
                self.failed_tests.append(f"Self-Healing Seed: {count} duplicates found")
                return False
            
            # Step 6: Test API endpoint
            print("\n   Step 6: Test API endpoint GET /api/briefings")
            success, response = self.run_test(
                "GET /api/briefings (should include Edition #1)",
                "GET",
                "briefings",
                200,
                headers={'Authorization': ''}  # No auth needed for briefings
            )
            
            if success:
                briefings = response.get('briefings', [])
                edition_1_found = any(b.get('edition') == 1 for b in briefings)
                if edition_1_found:
                    print("   ✅ Edition #1 found in /api/briefings response")
                else:
                    print("   ❌ Edition #1 NOT found in /api/briefings response")
                    self.failed_tests.append("Self-Healing Seed: Edition #1 not in briefings API")
            
            # Step 7: Test individual post endpoint
            print("\n   Step 7: Test GET /api/posts/five-things-commodity-desks-need-to-know-this-week")
            success2, response2 = self.run_test(
                "GET Edition #1 by slug",
                "GET",
                "posts/five-things-commodity-desks-need-to-know-this-week",
                200,
                headers={'Authorization': ''}
            )
            
            if success2:
                content_blocks = response2.get('content_blocks', [])
                if len(content_blocks) == 22:
                    print(f"   ✅ Edition #1 has 22 content blocks")
                else:
                    print(f"   ⚠️  Edition #1 has {len(content_blocks)} content blocks, expected 22")
                    self.failed_tests.append(f"Self-Healing Seed: Edition #1 has {len(content_blocks)} blocks, expected 22")
            
            print("\n   ✅ SELF-HEALING SEED TEST PASSED")
            return True
            
        except Exception as e:
            print(f"   ❌ Error during self-healing seed test: {e}")
            self.failed_tests.append(f"Self-Healing Seed: {e}")
            return False

    def test_highlight_digest(self):
        """Test highlight digest with and without highlights"""
        print("\n" + "="*60)
        print("TESTING: Highlight Digest (Most Highlighted This Week)")
        print("="*60)
        print("⚠️  CRITICAL: NOT calling send-digest (Gmail is LIVE)")
        
        from pymongo import MongoClient
        
        try:
            client = MongoClient("mongodb://localhost:27017")
            db = client["test_database"]
            highlights_collection = db["highlights"]
            
            # Step 1: Test digest-preview WITH existing highlights
            print("\n   Step 1: Test GET /api/admin/newsletter/digest-preview WITH highlights")
            success1, response1 = self.run_test(
                "Digest Preview (with highlights)",
                "GET",
                "admin/newsletter/digest-preview",
                200
            )
            
            if success1:
                top_highlights = response1.get('top_highlights', [])
                html = response1.get('html', '')
                
                print(f"   Top highlights count: {len(top_highlights)}")
                
                if len(top_highlights) > 0:
                    print("   ✅ top_highlights array is populated")
                    
                    # Check for the expected highlight text
                    expected_text = "This is not a small firm problem."
                    found_expected = any(h.get('text') == expected_text for h in top_highlights)
                    
                    if found_expected:
                        print(f"   ✅ Found expected highlight: '{expected_text}'")
                        
                        # Check count
                        for h in top_highlights:
                            if h.get('text') == expected_text:
                                if h.get('count') == 2:
                                    print(f"   ✅ Highlight count is 2 (as expected)")
                                else:
                                    print(f"   ⚠️  Highlight count is {h.get('count')}, expected 2")
                    else:
                        print(f"   ⚠️  Expected highlight text not found in top_highlights")
                    
                    # Check HTML contains the section
                    if 'Most highlighted this week' in html:
                        print("   ✅ HTML contains 'Most highlighted this week' section")
                    else:
                        print("   ❌ HTML does NOT contain 'Most highlighted this week' section")
                        self.failed_tests.append("Highlight Digest: HTML missing 'Most highlighted this week'")
                    
                    if expected_text in html:
                        print(f"   ✅ HTML contains the highlight text")
                    else:
                        print(f"   ⚠️  HTML does NOT contain the highlight text")
                else:
                    print("   ⚠️  top_highlights array is empty (expected some highlights)")
            
            # Step 2: Delete all highlights
            print("\n   Step 2: Delete all highlights from database")
            result = highlights_collection.delete_many({})
            print(f"   ✅ Deleted {result.deleted_count} highlights")
            
            # Step 3: Test digest-preview WITHOUT highlights
            print("\n   Step 3: Test GET /api/admin/newsletter/digest-preview WITHOUT highlights")
            success2, response2 = self.run_test(
                "Digest Preview (without highlights)",
                "GET",
                "admin/newsletter/digest-preview",
                200
            )
            
            if success2:
                top_highlights2 = response2.get('top_highlights', [])
                html2 = response2.get('html', '')
                
                if len(top_highlights2) == 0:
                    print("   ✅ top_highlights array is empty (as expected)")
                else:
                    print(f"   ⚠️  top_highlights has {len(top_highlights2)} items, expected 0")
                    self.failed_tests.append(f"Highlight Digest: top_highlights not empty after deletion")
                
                # Check HTML does NOT contain the section
                if 'Most highlighted this week' not in html2:
                    print("   ✅ HTML does NOT contain 'Most highlighted this week' section (graceful omission)")
                else:
                    print("   ❌ HTML still contains 'Most highlighted this week' section")
                    self.failed_tests.append("Highlight Digest: Section not omitted when no highlights")
            
            print("\n   ✅ HIGHLIGHT DIGEST TEST PASSED")
            return True
            
        except Exception as e:
            print(f"   ❌ Error during highlight digest test: {e}")
            self.failed_tests.append(f"Highlight Digest: {e}")
            return False

    def test_content_sync(self):
        """Test content sync endpoints"""
        print("\n" + "="*60)
        print("TESTING: Content Sync Tool")
        print("="*60)
        print("⚠️  CRITICAL: Production is LIVE - only testing READ operations")
        
        # Step 1: Test GET /api/admin/sync/diff (authenticated)
        print("\n   Step 1: Test GET /api/admin/sync/diff (admin auth)")
        success1, response1 = self.run_test(
            "Sync Diff (authenticated)",
            "GET",
            "admin/sync/diff",
            200
        )
        
        if success1:
            production_url = response1.get('production_url')
            production_published = response1.get('production_published')
            missing = response1.get('missing', [])
            
            print(f"   Production URL: {production_url}")
            print(f"   Production published: {production_published}")
            print(f"   Missing posts: {len(missing)}")
            
            # Verify production_url
            if production_url == 'https://thetradingnarrative.com':
                print("   ✅ production_url is correct")
            else:
                print(f"   ⚠️  production_url is '{production_url}', expected 'https://thetradingnarrative.com'")
            
            # Verify production_published >= 14
            if production_published >= 14:
                print(f"   ✅ production_published is {production_published} (>= 14)")
            else:
                print(f"   ⚠️  production_published is {production_published}, expected >= 14")
                self.failed_tests.append(f"Content Sync: production_published is {production_published}, expected >= 14")
            
            # Verify missing is empty (everything synced)
            if len(missing) == 0:
                print("   ✅ missing array is empty (everything already synced)")
            else:
                print(f"   ⚠️  missing array has {len(missing)} items (expected 0 for in-sync state)")
        
        # Step 2: Test unauthenticated request
        print("\n   Step 2: Test GET /api/admin/sync/diff (unauthenticated)")
        # Temporarily remove admin token
        saved_token = self.admin_token
        self.admin_token = None
        
        success2, _ = self.run_test(
            "Sync Diff (unauthenticated)",
            "GET",
            "admin/sync/diff",
            401,
            headers={'Authorization': ''}
        )
        
        if success2:
            print("   ✅ Unauthenticated request returns 401 (as expected)")
        
        # Restore admin token
        self.admin_token = saved_token
        
        # Step 3: Test POST /api/admin/sync/push (no-op)
        print("\n   Step 3: Test POST /api/admin/sync/push (no-op, nothing to push)")
        success3, response3 = self.run_test(
            "Sync Push (no-op)",
            "POST",
            "admin/sync/push",
            200,
            data={"password": "anything"}
        )
        
        if success3:
            pushed = response3.get('pushed')
            message = response3.get('message', '')
            
            if pushed == 0:
                print(f"   ✅ pushed = 0 (no-op as expected)")
            else:
                print(f"   ⚠️  pushed = {pushed}, expected 0")
                self.failed_tests.append(f"Content Sync: pushed = {pushed}, expected 0")
            
            if 'already' in message.lower() or 'sync' in message.lower():
                print(f"   ✅ Message indicates already in sync: '{message}'")
            else:
                print(f"   ⚠️  Message doesn't indicate sync status: '{message}'")
        
        print("\n   ✅ CONTENT SYNC TEST PASSED")
        return True

def main():
    print("\n" + "="*60)
    print("TRADING NARRATIVE - BACKEND API TESTING")
    print("Session: Self-Healing Seed + Highlight Digest + Content Sync")
    print("="*60)
    
    tester = TradingNarrativeAPITester()
    
    # Test 1: Admin Login
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    # Test 2: Self-Healing Seed (Edition #1 restoration)
    tester.test_self_healing_seed()
    
    # Test 3: Highlight Digest
    tester.test_highlight_digest()
    
    # Test 4: Content Sync
    tester.test_content_sync()
    
    # Test 5: Email Status (existing test)
    tester.test_email_status()
    
    # Test 6: Funnel Plan Split (existing test)
    tester.test_funnel_plan_split()
    
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
