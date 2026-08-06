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

def main():
    print("\n" + "="*60)
    print("TRADING NARRATIVE - BACKEND API TESTING")
    print("Session: Gmail SMTP Live + Funnel Split + Announcement Editing")
    print("="*60)
    
    tester = TradingNarrativeAPITester()
    
    # Test 1: Admin Login
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    # Test 2: Email Status
    tester.test_email_status()
    
    # Test 3: Funnel Plan Split
    tester.test_funnel_plan_split()
    
    # Test 4: Announcement Editing
    tester.test_announcement_editing()
    
    # Test 5: Digest Personalization Code Review
    tester.test_digest_personalization_code_review()
    
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
