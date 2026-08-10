#!/usr/bin/env python3
"""
Phase 38 Testing: Edition #2 briefing, new pricing, early supporter, audio gating
Tests the specific features implemented in Phase 38.
"""
import requests
import sys
import uuid
from datetime import datetime

BASE_URL = "https://insight-hub-484.preview.emergentagent.com/api"

class Phase38Test:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.free_user_token = None
        self.free_user_email = None
        self.early_supporter_token = None
        self.early_supporter_email = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, expected=None, got=None, details=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            msg = f"{name}"
            if expected and got:
                msg += f" (expected {expected}, got {got})"
            if details:
                msg += f" - {details}"
            self.failed_tests.append(msg)
            print(f"❌ {msg}")
        return success

    def api_call(self, method, endpoint, expected_status, data=None, token=None, no_auth=False, return_headers=False):
        """Make API call and return (success, response_data) or (success, response_data, headers)"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if not no_auth and token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            else:
                return (False, {}, {}) if return_headers else (False, {})

            success = response.status_code == expected_status
            try:
                resp_data = response.json() if success else {}
            except:
                resp_data = {}
            
            if return_headers:
                return success, resp_data, dict(response.headers)
            return success, resp_data
        except Exception as e:
            print(f"   ⚠️  API call failed: {e}")
            return (False, {}, {}) if return_headers else (False, {})

    def test_billing_config(self):
        """Test GET /api/billing/config returns 4 plans with new pricing"""
        print("\n" + "="*60)
        print("TESTING: BILLING CONFIG (NEW PRICING)")
        print("="*60)
        
        success, resp = self.api_call('GET', 'billing/config', 200, no_auth=True)
        if not success:
            self.log_test("GET /api/billing/config", False, details="API call failed")
            return False
        
        plans_list = resp.get('plans', [])
        
        # Convert list to dict for easier lookup
        plans = {p['id']: p for p in plans_list}
        
        # Check all 4 plans exist
        expected_plans = ['monthly', 'annual', 'founding_monthly', 'founding']
        all_exist = all(plan in plans for plan in expected_plans)
        self.log_test("All 4 plans exist", all_exist, 
                     expected=expected_plans, got=list(plans.keys()))
        
        # Check monthly pricing
        monthly = plans.get('monthly', {})
        monthly_ok = (monthly.get('amount') == 1.04 and monthly.get('amount_inr') == 99.0)
        self.log_test("Monthly plan pricing ($1.04/₹99)", monthly_ok,
                     expected="$1.04/₹99", got=f"${monthly.get('amount')}/₹{monthly.get('amount_inr')}")
        
        # Check annual pricing
        annual = plans.get('annual', {})
        annual_ok = (annual.get('amount') == 10.50 and annual.get('amount_inr') == 999.0)
        self.log_test("Annual plan pricing ($10.50/₹999)", annual_ok,
                     expected="$10.50/₹999", got=f"${annual.get('amount')}/₹{annual.get('amount_inr')}")
        
        # Check founding_monthly pricing
        founding_monthly = plans.get('founding_monthly', {})
        founding_monthly_ok = (founding_monthly.get('amount') == 4.80 and founding_monthly.get('amount_inr') == 458.0)
        self.log_test("Founding Monthly plan pricing ($4.80/₹458)", founding_monthly_ok,
                     expected="$4.80/₹458", got=f"${founding_monthly.get('amount')}/₹{founding_monthly.get('amount_inr')}")
        
        # Check founding pricing
        founding = plans.get('founding', {})
        founding_ok = (founding.get('amount') == 57.69 and founding.get('amount_inr') == 5499.0)
        self.log_test("Founding plan pricing ($57.69/₹5499)", founding_ok,
                     expected="$57.69/₹5499", got=f"${founding.get('amount')}/₹{founding.get('amount_inr')}")
        
        return all_exist and monthly_ok and annual_ok and founding_monthly_ok and founding_ok

    def test_briefings(self):
        """Test GET /api/briefings lists edition 2 and edition 1, both tier=free"""
        print("\n" + "="*60)
        print("TESTING: BRIEFINGS")
        print("="*60)
        
        success, resp = self.api_call('GET', 'briefings', 200, no_auth=True)
        if not success:
            self.log_test("GET /api/briefings", False, details="API call failed")
            return False
        
        briefings = resp.get('briefings', [])
        
        # Check at least 2 briefings exist
        has_briefings = len(briefings) >= 2
        self.log_test(f"At least 2 briefings exist", has_briefings,
                     expected=">=2", got=len(briefings))
        
        # Find edition 1 and 2
        edition_1 = next((b for b in briefings if b.get('edition') == 1), None)
        edition_2 = next((b for b in briefings if b.get('edition') == 2), None)
        
        self.log_test("Edition 1 exists", edition_1 is not None)
        self.log_test("Edition 2 exists", edition_2 is not None)
        
        if edition_1:
            self.log_test("Edition 1 is free tier", edition_1.get('tier') == 'free',
                         expected='free', got=edition_1.get('tier'))
        
        if edition_2:
            self.log_test("Edition 2 is free tier", edition_2.get('tier') == 'free',
                         expected='free', got=edition_2.get('tier'))
            self.log_test("Edition 2 slug is oils-sharp-slide...", 
                         edition_2.get('slug') == 'oils-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners',
                         expected='oils-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners',
                         got=edition_2.get('slug'))
        
        return has_briefings and edition_1 and edition_2

    def test_edition2_post(self):
        """Test GET /api/posts/oils-sharp-slide... returns full content with ## headings"""
        print("\n" + "="*60)
        print("TESTING: EDITION #2 POST")
        print("="*60)
        
        slug = 'oils-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners'
        success, resp = self.api_call('GET', f'posts/{slug}', 200, no_auth=True)
        
        if not success:
            self.log_test(f"GET /api/posts/{slug}", False, details="API call failed")
            return False
        
        self.log_test(f"Edition #2 post accessible", True)
        
        # Check edition number
        edition_ok = resp.get('edition') == 2
        self.log_test("Edition number is 2", edition_ok, expected=2, got=resp.get('edition'))
        
        # Check tier is free
        tier_ok = resp.get('tier') == 'free'
        self.log_test("Tier is free", tier_ok, expected='free', got=resp.get('tier'))
        
        # Check content_blocks exist and have content
        blocks = resp.get('content_blocks', [])
        has_blocks = len(blocks) > 0
        self.log_test(f"Has content blocks ({len(blocks)} blocks)", has_blocks)
        
        # Check for ## section headings in content
        has_headings = False
        if blocks:
            # Blocks can be strings or dicts
            if isinstance(blocks[0], str):
                content_text = ' '.join(blocks)
            else:
                content_text = ' '.join([b.get('text', '') for b in blocks if isinstance(b, dict)])
            has_headings = '##' in content_text
        self.log_test("Content has ## section headings", has_headings)
        
        # Check not locked
        is_locked = resp.get('is_locked', True)
        self.log_test("Post is not locked (free tier)", not is_locked, expected=False, got=is_locked)
        
        return edition_ok and tier_ok and has_blocks and not is_locked

    def test_premium_gating_anonymous(self):
        """Test premium posts are locked for anonymous users"""
        print("\n" + "="*60)
        print("TESTING: PREMIUM GATING (ANONYMOUS)")
        print("="*60)
        
        premium_slugs = [
            'freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr',
            '170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum',
            'delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile'
        ]
        
        all_locked = True
        for slug in premium_slugs:
            success, resp = self.api_call('GET', f'posts/{slug}', 200, no_auth=True)
            if success:
                is_locked = resp.get('is_locked', False)
                shown_blocks = resp.get('shown_blocks', 0)
                
                # Should be locked with only 3 preview blocks
                locked_ok = is_locked and shown_blocks == 3
                self.log_test(f"Premium post {slug[:30]}... is locked (3 blocks)", locked_ok,
                             expected="locked, 3 blocks", got=f"locked={is_locked}, blocks={shown_blocks}")
                all_locked = all_locked and locked_ok
            else:
                self.log_test(f"Premium post {slug[:30]}... accessible", False, details="404 or error")
                all_locked = False
        
        return all_locked

    def test_early_supporter(self):
        """Test early supporter registration and premium post access"""
        print("\n" + "="*60)
        print("TESTING: EARLY SUPPORTER")
        print("="*60)
        
        # Register a new user (should be early_supporter=true if <50 users)
        test_email = f"early-test-{uuid.uuid4().hex[:8]}@example.com"
        success, resp = self.api_call('POST', 'auth/register', 200,
            {'email': test_email, 'password': 'Test@123', 'name': 'Early Tester'}, no_auth=True)
        
        if not success or not resp.get('token'):
            self.log_test("Register early supporter user", False, details="Registration failed")
            return False
        
        self.early_supporter_token = resp['token']
        self.early_supporter_email = test_email
        self.log_test("Register early supporter user", True)
        
        # Check /auth/me shows early_supporter=true
        success, resp = self.api_call('GET', 'auth/me', 200, token=self.early_supporter_token)
        if success:
            user = resp.get('user', {})
            is_early = user.get('early_supporter', False)
            self.log_test("User has early_supporter=true", is_early, expected=True, got=is_early)
        else:
            self.log_test("GET /auth/me for early supporter", False)
            return False
        
        # Test access to premium post (should be unlocked if in first 5 published)
        # Note: Edition #2 is NOT in first 5, so it won't have early_unlock (but it's free anyway)
        # Let's test with a premium post that IS in first 5
        premium_slug = 'delivering-a-power-trading-desk-system-compliance-lifecycle-design-and-why-agile'
        success, resp = self.api_call('GET', f'posts/{premium_slug}', 200, token=self.early_supporter_token)
        
        if success:
            is_locked = resp.get('is_locked', True)
            early_unlock = resp.get('early_unlock', False)
            total_blocks = resp.get('total_blocks', 0)
            shown_blocks = resp.get('shown_blocks', 0)
            
            # If this post is in first 5 published, it should be unlocked with early_unlock=true
            if early_unlock:
                self.log_test(f"Early supporter unlocks premium post", not is_locked and early_unlock,
                             expected="unlocked, early_unlock=true", 
                             got=f"locked={is_locked}, early_unlock={early_unlock}")
            else:
                # If not in first 5, should still be locked
                self.log_test(f"Premium post not in first 5 (still locked)", is_locked,
                             expected="locked (not in first 5)", got=f"locked={is_locked}")
        
        return True

    def test_audio_gating(self):
        """Test audio narration gating: anonymous=401, free user=20s clip"""
        print("\n" + "="*60)
        print("TESTING: AUDIO GATING")
        print("="*60)
        
        # Use edition #2 slug for audio test
        slug = 'oils-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners'
        
        # Test 1: Anonymous user should get 401
        try:
            url = f"{self.base_url}/posts/{slug}/audio"
            response = requests.get(url, timeout=15)
            anon_401 = response.status_code == 401
            self.log_test("Anonymous audio request returns 401", anon_401,
                         expected=401, got=response.status_code)
        except Exception as e:
            self.log_test("Anonymous audio request", False, details=str(e))
            anon_401 = False
        
        # Test 2: Free user should get 200 with 160000 bytes and X-Audio-Scope: clip
        if not self.free_user_token:
            # Create a free user
            test_email = f"free-audio-test-{uuid.uuid4().hex[:8]}@example.com"
            success, resp = self.api_call('POST', 'auth/register', 200,
                {'email': test_email, 'password': 'Test@123', 'name': 'Free Audio Tester'}, no_auth=True)
            if success and resp.get('token'):
                self.free_user_token = resp['token']
                self.free_user_email = test_email
        
        if self.free_user_token:
            try:
                url = f"{self.base_url}/posts/{slug}/audio"
                headers = {'Authorization': f'Bearer {self.free_user_token}'}
                response = requests.get(url, headers=headers, timeout=15)
                
                free_200 = response.status_code == 200
                self.log_test("Free user audio request returns 200", free_200,
                             expected=200, got=response.status_code)
                
                if free_200:
                    content_length = len(response.content)
                    length_ok = content_length == 160000
                    self.log_test("Audio clip is exactly 160000 bytes", length_ok,
                                 expected=160000, got=content_length)
                    
                    scope_header = response.headers.get('X-Audio-Scope', '')
                    scope_ok = scope_header == 'clip'
                    self.log_test("X-Audio-Scope header is 'clip'", scope_ok,
                                 expected='clip', got=scope_header)
                    
                    return anon_401 and free_200 and length_ok and scope_ok
            except Exception as e:
                self.log_test("Free user audio request", False, details=str(e))
                return False
        
        return anon_401

    def test_razorpay_checkout(self):
        """Test POST /api/billing/razorpay/checkout creates order with founding_monthly plan"""
        print("\n" + "="*60)
        print("TESTING: RAZORPAY CHECKOUT")
        print("="*60)
        
        # Need an authenticated user
        if not self.free_user_token:
            test_email = f"razorpay-test-{uuid.uuid4().hex[:8]}@example.com"
            success, resp = self.api_call('POST', 'auth/register', 200,
                {'email': test_email, 'password': 'Test@123', 'name': 'Razorpay Tester'}, no_auth=True)
            if success and resp.get('token'):
                self.free_user_token = resp['token']
                self.free_user_email = test_email
        
        if not self.free_user_token:
            self.log_test("Razorpay checkout test", False, details="No authenticated user")
            return False
        
        # Create checkout order for founding_monthly plan
        success, resp = self.api_call('POST', 'billing/razorpay/checkout', 200,
            {'plan': 'founding_monthly'}, token=self.free_user_token)
        
        if not success:
            self.log_test("POST /api/billing/razorpay/checkout", False, details="API call failed")
            return False
        
        self.log_test("Razorpay checkout order created", True)
        
        # Check order amount is 45800 paise (₹458)
        amount = resp.get('amount', 0)
        amount_ok = amount == 45800
        self.log_test("Order amount is 45800 paise (₹458)", amount_ok,
                     expected=45800, got=amount)
        
        # Check order_id or ref_id exists
        order_id = resp.get('order_id') or resp.get('ref_id', '')
        has_order_id = len(order_id) > 0
        self.log_test("Order has ID", has_order_id)
        
        return amount_ok and has_order_id

    def test_regression_auth(self):
        """Test basic auth endpoints still work"""
        print("\n" + "="*60)
        print("TESTING: REGRESSION - AUTH")
        print("="*60)
        
        # Test register
        test_email = f"regression-{uuid.uuid4().hex[:8]}@example.com"
        success, resp = self.api_call('POST', 'auth/register', 200,
            {'email': test_email, 'password': 'Test@123', 'name': 'Regression Tester'}, no_auth=True)
        
        register_ok = success and resp.get('token') is not None
        self.log_test("POST /api/auth/register", register_ok)
        
        if not register_ok:
            return False
        
        token = resp['token']
        
        # Test login
        success, resp = self.api_call('POST', 'auth/login', 200,
            {'email': test_email, 'password': 'Test@123'}, no_auth=True)
        login_ok = success and resp.get('token') is not None
        self.log_test("POST /api/auth/login", login_ok)
        
        # Test /auth/me
        success, resp = self.api_call('GET', 'auth/me', 200, token=token)
        me_ok = success and resp.get('user', {}).get('email') == test_email
        self.log_test("GET /api/auth/me", me_ok)
        
        # Test streak fields exist
        user = resp.get('user', {})
        has_streak_fields = 'current_streak' in user and 'longest_streak' in user
        self.log_test("User has streak fields", has_streak_fields)
        
        return register_ok and login_ok and me_ok and has_streak_fields

    def test_regression_posts(self):
        """Test GET /api/posts still works"""
        print("\n" + "="*60)
        print("TESTING: REGRESSION - POSTS")
        print("="*60)
        
        success, resp = self.api_call('GET', 'posts', 200, no_auth=True)
        
        if not success:
            self.log_test("GET /api/posts", False)
            return False
        
        posts = resp.get('posts', [])
        has_posts = len(posts) > 0
        self.log_test("GET /api/posts returns posts", has_posts, got=f"{len(posts)} posts")
        
        return has_posts

    def test_regression_reading_streak(self):
        """Test POST /api/users/streak/read still works"""
        print("\n" + "="*60)
        print("TESTING: REGRESSION - READING STREAK")
        print("="*60)
        
        if not self.free_user_token:
            test_email = f"streak-test-{uuid.uuid4().hex[:8]}@example.com"
            success, resp = self.api_call('POST', 'auth/register', 200,
                {'email': test_email, 'password': 'Test@123', 'name': 'Streak Tester'}, no_auth=True)
            if success and resp.get('token'):
                self.free_user_token = resp['token']
        
        if not self.free_user_token:
            self.log_test("Reading streak test", False, details="No authenticated user")
            return False
        
        success, resp = self.api_call('POST', 'users/streak/read', 200,
            {'tz_offset_minutes': 0}, token=self.free_user_token)
        
        if not success:
            self.log_test("POST /api/users/streak/read", False)
            return False
        
        self.log_test("POST /api/users/streak/read", True)
        
        # Check response has streak data
        has_streak_data = 'current_streak' in resp and 'longest_streak' in resp
        self.log_test("Response has streak data", has_streak_data)
        
        return has_streak_data

    def cleanup(self):
        """Clean up test users"""
        print("\n" + "="*60)
        print("CLEANUP")
        print("="*60)
        
        # Note: In a real scenario, we'd delete test users here
        # But since we don't have a delete user endpoint, we'll just log
        if self.early_supporter_email:
            print(f"   Test user created: {self.early_supporter_email}")
        if self.free_user_email:
            print(f"   Test user created: {self.free_user_email}")

    def run_all_tests(self):
        """Run all Phase 38 tests"""
        print("\n" + "="*70)
        print("PHASE 38 BACKEND TESTING")
        print("="*70)
        
        # Run all tests
        self.test_billing_config()
        self.test_briefings()
        self.test_edition2_post()
        self.test_premium_gating_anonymous()
        self.test_early_supporter()
        self.test_audio_gating()
        self.test_razorpay_checkout()
        self.test_regression_auth()
        self.test_regression_posts()
        self.test_regression_reading_streak()
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        return 0 if self.tests_passed == self.tests_run else 1


def main():
    tester = Phase38Test()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
