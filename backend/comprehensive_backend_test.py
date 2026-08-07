#!/usr/bin/env python3
"""
Comprehensive Backend Regression Test for The Trading Narrative
Tests all refactored routes to ensure nothing broke during the modularization.
"""
import requests
import sys
import uuid
from datetime import datetime

BASE_URL = "https://insight-hub-484.preview.emergentagent.com/api"

class TradingNarrativeRegressionTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.test_user_token = None
        self.test_user_email = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_data_to_cleanup = {
            'posts': [],
            'threads': [],
            'announcements': [],
            'newsletter_emails': []
        }

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

    def api_call(self, method, endpoint, expected_status, data=None, token=None, no_auth=False):
        """Make API call and return (success, response_data)"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if not no_auth:
            if token:
                headers['Authorization'] = f'Bearer {token}'
            elif self.admin_token:
                headers['Authorization'] = f'Bearer {self.admin_token}'

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
                return False, {}

            success = response.status_code == expected_status
            try:
                return success, response.json() if success else {}
            except:
                return success, {}
        except Exception as e:
            print(f"   ⚠️  API call failed: {e}")
            return False, {}

    # ==================== AUTH TESTS ====================
    
    def test_auth(self):
        """Test all auth routes"""
        print("\n" + "="*60)
        print("TESTING: AUTH ROUTES")
        print("="*60)
        
        # 1. Admin login
        success, resp = self.api_call('POST', 'auth/login', 200, 
            {'email': 'admin@tradingnarrative.com', 'password': 'Admin@2025'}, no_auth=True)
        if success and resp.get('token'):
            self.admin_token = resp['token']
            self.log_test("Admin login", True)
        else:
            self.log_test("Admin login", False, details="No token returned")
            return False
        
        # 2. GET /auth/me
        success, resp = self.api_call('GET', 'auth/me', 200)
        self.log_test("GET /auth/me", success and resp.get('user', {}).get('email') == 'admin@tradingnarrative.com')
        
        # 3. Register new user
        test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_email = test_email
        success, resp = self.api_call('POST', 'auth/register', 200,
            {'email': test_email, 'name': 'Test User', 'password': 'Test@123'}, no_auth=True)
        if success and resp.get('token'):
            self.test_user_token = resp['token']
            self.log_test("Register new user", True)
        else:
            self.log_test("Register new user", False)
        
        # 4. Magic link request
        success, resp = self.api_call('POST', 'auth/magic-link/request', 200,
            {'email': test_email}, no_auth=True)
        self.log_test("Magic link request", success and 'magic_link' in resp)
        
        # 5. Password reset request
        success, resp = self.api_call('POST', 'auth/password-reset/request', 200,
            {'email': test_email}, no_auth=True)
        self.log_test("Password reset request", success and 'reset_link' in resp)
        
        return True

    # ==================== POSTS TESTS ====================
    
    def test_posts(self):
        """Test posts routes"""
        print("\n" + "="*60)
        print("TESTING: POSTS ROUTES")
        print("="*60)
        
        # 1. GET /categories
        success, resp = self.api_call('GET', 'categories', 200, no_auth=True)
        categories = resp if isinstance(resp, list) else resp.get('categories', [])
        has_tech = any(c.get('slug') == 'tech-business' for c in categories)
        self.log_test("GET /categories", success and has_tech)
        
        # 2. GET /posts (all)
        success, resp = self.api_call('GET', 'posts', 200, no_auth=True)
        posts = resp.get('posts', [])
        self.log_test("GET /posts", success and len(posts) > 0)
        
        # 3. GET /posts?category=tech-business (should include freight article)
        success, resp = self.api_call('GET', 'posts?category=tech-business', 200, no_auth=True)
        posts = resp.get('posts', [])
        freight_found = any('freight' in p.get('slug', '').lower() for p in posts)
        self.log_test("GET /posts?category=tech-business (freight article)", success and freight_found)
        
        # 4. GET /posts?tier=premium
        success, resp = self.api_call('GET', 'posts?tier=premium', 200, no_auth=True)
        self.log_test("GET /posts?tier=premium", success)
        
        # 5. GET /posts?featured=true
        success, resp = self.api_call('GET', 'posts?featured=true', 200, no_auth=True)
        self.log_test("GET /posts?featured=true", success)
        
        # 6. GET /posts?q=freight
        success, resp = self.api_call('GET', 'posts?q=freight', 200, no_auth=True)
        self.log_test("GET /posts?q=freight", success)
        
        # 7. GET specific freight article
        freight_slug = 'freight-management-and-tracking-visibility-how-digital-platforms-and-ai-are-rewr'
        success, resp = self.api_call('GET', f'posts/{freight_slug}', 200, no_auth=True)
        is_locked = resp.get('is_locked', False)
        shown_blocks = resp.get('shown_blocks', 0)
        self.log_test(f"GET /posts/{freight_slug[:30]}...", success)
        self.log_test("Freight article paywall (non-premium)", is_locked and shown_blocks == 3)
        
        # 8. GET /briefings
        success, resp = self.api_call('GET', 'briefings', 200, no_auth=True)
        briefings = resp.get('briefings', [])
        self.log_test("GET /briefings", success and len(briefings) > 0)
        
        # 9. GET /recommendations
        success, resp = self.api_call('GET', 'recommendations', 200, no_auth=True)
        self.log_test("GET /recommendations", success)
        
        # 10. GET /sitemap.xml
        success, _ = self.api_call('GET', 'sitemap.xml', 200, no_auth=True)
        self.log_test("GET /sitemap.xml", success)
        
        # 11. GET /health
        success, resp = self.api_call('GET', 'health', 200, no_auth=True)
        self.log_test("GET /health", success and resp.get('status') == 'ok')

    # ==================== COMMENTS & BOOKMARKS TESTS ====================
    
    def test_comments_bookmarks(self):
        """Test comments, notifications, bookmarks"""
        print("\n" + "="*60)
        print("TESTING: COMMENTS, NOTIFICATIONS, BOOKMARKS")
        print("="*60)
        
        # Get a post to test with
        success, resp = self.api_call('GET', 'posts?limit=1', 200, no_auth=True)
        if not success or not resp.get('posts'):
            print("   ⚠️  No posts available for testing")
            return
        
        post = resp['posts'][0]
        post_slug = post['slug']
        post_id = post['id']
        
        # 1. GET comments (should work without auth)
        success, resp = self.api_call('GET', f'posts/{post_slug}/comments', 200, no_auth=True)
        self.log_test(f"GET /posts/{post_slug}/comments", success)
        
        # 2. POST comment (requires premium - should fail for test user)
        success, resp = self.api_call('POST', f'posts/{post_slug}/comments', 403,
            {'body': 'Test comment'}, token=self.test_user_token)
        self.log_test("POST comment (non-premium user blocked)", success)
        
        # 3. GET /notifications (requires auth)
        success, resp = self.api_call('GET', 'notifications', 200, token=self.test_user_token)
        self.log_test("GET /notifications", success)
        
        # 4. POST /notifications/mark-read
        success, resp = self.api_call('POST', 'notifications/mark-read', 200, token=self.test_user_token)
        self.log_test("POST /notifications/mark-read", success)
        
        # 5. GET /bookmarks
        success, resp = self.api_call('GET', 'bookmarks', 200, token=self.test_user_token)
        self.log_test("GET /bookmarks", success)
        
        # 6. POST /bookmarks/toggle (add)
        success, resp = self.api_call('POST', 'bookmarks/toggle', 200,
            {'post_id': post_id}, token=self.test_user_token)
        self.log_test("POST /bookmarks/toggle (add)", success and resp.get('bookmarked') == True)
        
        # 7. POST /bookmarks/toggle (remove)
        success, resp = self.api_call('POST', 'bookmarks/toggle', 200,
            {'post_id': post_id}, token=self.test_user_token)
        self.log_test("POST /bookmarks/toggle (remove)", success and resp.get('bookmarked') == False)

    # ==================== BILLING TESTS ====================
    
    def test_billing(self):
        """Test billing routes"""
        print("\n" + "="*60)
        print("TESTING: BILLING ROUTES")
        print("="*60)
        
        # 1. GET /billing/config
        success, resp = self.api_call('GET', 'billing/config', 200, no_auth=True)
        razorpay_enabled = resp.get('razorpay_enabled', False)
        plans = resp.get('plans', [])
        self.log_test("GET /billing/config", success and len(plans) == 2)
        self.log_test("Razorpay enabled in config", razorpay_enabled == True)
        
        # 2. GET /billing/subscription (test user - should have none)
        success, resp = self.api_call('GET', 'billing/subscription', 200, token=self.test_user_token)
        self.log_test("GET /billing/subscription (no subscription)", success and resp.get('subscription') is None)
        
        # 3. GET /billing/invoices
        success, resp = self.api_call('GET', 'billing/invoices', 200, token=self.test_user_token)
        self.log_test("GET /billing/invoices", success)
        
        # 4. POST /billing/checkout (Stripe) - just check it returns checkout_url
        # Note: Not completing payment to avoid charges
        success, resp = self.api_call('POST', 'billing/checkout', 200,
            {'plan': 'monthly'}, token=self.test_user_token)
        has_checkout_url = 'checkout_url' in resp or 'mock' in resp
        self.log_test("POST /billing/checkout (Stripe)", success and has_checkout_url)
        
        # 5. POST /billing/razorpay/checkout
        success, resp = self.api_call('POST', 'billing/razorpay/checkout', 200,
            {'plan': 'monthly'}, token=self.test_user_token)
        kind = resp.get('kind', '')
        self.log_test("POST /billing/razorpay/checkout", success)
        self.log_test("Razorpay checkout kind=order (autopay not enabled)", kind == 'order')

    # ==================== NEWSLETTER TESTS ====================
    
    def test_newsletter(self):
        """Test newsletter routes"""
        print("\n" + "="*60)
        print("TESTING: NEWSLETTER ROUTES")
        print("="*60)
        
        # Use throwaway email for testing
        throwaway_email = f"ttn-test-{uuid.uuid4().hex[:8]}@example.com"
        self.test_data_to_cleanup['newsletter_emails'].append(throwaway_email)
        
        # 1. POST /newsletter/subscribe
        success, resp = self.api_call('POST', 'newsletter/subscribe', 200,
            {'email': throwaway_email, 'source': 'test'}, no_auth=True)
        self.log_test("POST /newsletter/subscribe", success and resp.get('ok') == True)
        
        # 2. GET /newsletter/my-preferences (test user)
        success, resp = self.api_call('GET', 'newsletter/my-preferences', 200, token=self.test_user_token)
        self.log_test("GET /newsletter/my-preferences", success)
        
        # 3. POST /newsletter/my-preferences
        success, resp = self.api_call('POST', 'newsletter/my-preferences', 200,
            {'subscribed': True, 'categories': ['tech-business', 'finance']}, token=self.test_user_token)
        self.log_test("POST /newsletter/my-preferences", success)
        
        # 4. GET /newsletter/unsubscribe (invalid token - should return 400 HTML)
        success, _ = self.api_call('GET', 'newsletter/unsubscribe?email=test@example.com&token=invalid', 400, no_auth=True)
        self.log_test("GET /newsletter/unsubscribe (invalid token)", success)

    # ==================== ANALYTICS TESTS ====================
    
    def test_analytics(self):
        """Test analytics routes"""
        print("\n" + "="*60)
        print("TESTING: ANALYTICS ROUTES")
        print("="*60)
        
        # 1. POST /analytics/track (pageview with first_visit)
        success, resp = self.api_call('POST', 'analytics/track', 200,
            {'event': 'pageview', 'path': '/', 'sid': f'test-{uuid.uuid4().hex[:8]}',
             'meta': {'first_visit': True, 'referrer': 'https://google.com'}}, no_auth=True)
        self.log_test("POST /analytics/track (pageview)", success)
        
        # 2. GET /admin/traffic
        success, resp = self.api_call('GET', 'admin/traffic?days=30', 200)
        self.log_test("GET /admin/traffic", success)
        
        # 3. GET /admin/traffic/export (CSV)
        success, _ = self.api_call('GET', 'admin/traffic/export?days=30', 200)
        self.log_test("GET /admin/traffic/export (CSV)", success)
        
        # 4. GET /admin/funnel
        success, resp = self.api_call('GET', 'admin/funnel?days=30', 200)
        overall = resp.get('overall', {})
        has_split = 'conversions_monthly' in overall and 'conversions_annual' in overall
        self.log_test("GET /admin/funnel", success)
        self.log_test("Funnel has monthly/annual split", has_split)

    # ==================== COMMUNITY TESTS ====================
    
    def test_community(self):
        """Test community routes"""
        print("\n" + "="*60)
        print("TESTING: COMMUNITY ROUTES")
        print("="*60)
        
        # Community requires premium - test user is not premium, so should get 403
        
        # 1. GET /community/announcements (non-premium - should fail)
        success, _ = self.api_call('GET', 'community/announcements', 403, token=self.test_user_token)
        self.log_test("GET /community/announcements (non-premium blocked)", success)
        
        # 2. GET /community/threads (non-premium - should fail)
        success, _ = self.api_call('GET', 'community/threads', 403, token=self.test_user_token)
        self.log_test("GET /community/threads (non-premium blocked)", success)
        
        # Admin can access community
        # 3. GET /community/announcements (admin)
        success, resp = self.api_call('GET', 'community/announcements', 200)
        self.log_test("GET /community/announcements (admin)", success)
        
        # 4. GET /community/threads (admin)
        success, resp = self.api_call('GET', 'community/threads', 200)
        threads = resp.get('threads', [])
        self.log_test("GET /community/threads (admin)", success)
        
        # 5. POST /community/threads (admin - create test thread)
        success, resp = self.api_call('POST', 'community/threads', 200,
            {'title': 'Test Thread - DELETE ME', 'body': 'This is a test thread created by automated testing.'})
        if success and resp.get('id'):
            thread_id = resp['id']
            self.test_data_to_cleanup['threads'].append(thread_id)
            self.log_test("POST /community/threads (create)", True)
            
            # 6. GET /community/threads/{tid}
            success, resp = self.api_call('GET', f'community/threads/{thread_id}', 200)
            self.log_test(f"GET /community/threads/{thread_id}", success)
            
            # 7. POST /community/threads/{tid}/replies
            success, resp = self.api_call('POST', f'community/threads/{thread_id}/replies', 200,
                {'body': 'Test reply'})
            self.log_test("POST /community/threads/{tid}/replies", success)
            
            # 8. POST /community/threads/{tid}/pin
            success, resp = self.api_call('POST', f'community/threads/{thread_id}/pin', 200)
            self.log_test("POST /community/threads/{tid}/pin", success and resp.get('pinned') == True)
            
            # 9. POST /community/threads/{tid}/lock
            success, resp = self.api_call('POST', f'community/threads/{thread_id}/lock', 200)
            self.log_test("POST /community/threads/{tid}/lock", success and resp.get('locked') == True)
        else:
            self.log_test("POST /community/threads (create)", False)
        
        # 10. POST /community/announcements (admin - create test announcement)
        success, resp = self.api_call('POST', 'community/announcements', 200,
            {'title': 'Test Announcement - DELETE ME', 'body': 'This is a test announcement.'})
        if success and resp.get('id'):
            ann_id = resp['id']
            self.test_data_to_cleanup['announcements'].append(ann_id)
            self.log_test("POST /community/announcements (create)", True)
            
            # 11. PUT /community/announcements/{aid}
            success, resp = self.api_call('PUT', f'community/announcements/{ann_id}', 200,
                {'title': 'Test Announcement - EDITED', 'body': 'This is an edited test announcement.'})
            self.log_test(f"PUT /community/announcements/{ann_id}", success)
        else:
            self.log_test("POST /community/announcements (create)", False)

    # ==================== ADMIN TESTS ====================
    
    def test_admin(self):
        """Test admin routes"""
        print("\n" + "="*60)
        print("TESTING: ADMIN ROUTES")
        print("="*60)
        
        # 1. GET /admin/posts
        success, resp = self.api_call('GET', 'admin/posts', 200)
        posts = resp.get('posts', [])
        self.log_test("GET /admin/posts", success and len(posts) > 0)
        
        # 2. POST /admin/posts (create test post)
        success, resp = self.api_call('POST', 'admin/posts', 200, {
            'title': 'Test Post - DELETE ME',
            'excerpt': 'This is a test post created by automated testing.',
            'category': 'tech-business',
            'tier': 'free',
            'cover_image': 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d',
            'content_blocks': [
                {'type': 'paragraph', 'content': 'This is a test paragraph.'},
                {'type': 'paragraph', 'content': 'This is another test paragraph.'}
            ],
            'tags': ['test'],
            'featured': False,
            'status': 'draft',
            'publish_at': None,
            'edition': None
        })
        if success and resp.get('id'):
            post_id = resp['id']
            self.test_data_to_cleanup['posts'].append(post_id)
            self.log_test("POST /admin/posts (create)", True)
            
            # 3. GET /admin/posts/{post_id}
            success, resp = self.api_call('GET', f'admin/posts/{post_id}', 200)
            self.log_test(f"GET /admin/posts/{post_id}", success)
            
            # 4. PUT /admin/posts/{post_id}
            success, resp = self.api_call('PUT', f'admin/posts/{post_id}', 200, {
                'title': 'Test Post - EDITED',
                'excerpt': 'This is an edited test post.',
                'category': 'tech-business',
                'tier': 'free',
                'cover_image': 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d',
                'content_blocks': [
                    {'type': 'paragraph', 'content': 'This is an edited test paragraph.'}
                ],
                'tags': ['test', 'edited'],
                'featured': False,
                'status': 'draft',
                'publish_at': None,
                'edition': None
            })
            self.log_test(f"PUT /admin/posts/{post_id}", success)
        else:
            self.log_test("POST /admin/posts (create)", False)
        
        # 5. GET /admin/analytics/stats
        success, resp = self.api_call('GET', 'admin/analytics/stats', 200)
        has_stats = 'pageviews' in resp and 'newsletter_subscribers' in resp
        self.log_test("GET /admin/analytics/stats", success and has_stats)
        
        # 6. GET /admin/email/status
        success, resp = self.api_call('GET', 'admin/email/status', 200)
        enabled = resp.get('enabled', False)
        provider = resp.get('provider', '')
        self.log_test("GET /admin/email/status", success)
        self.log_test("Email status shows gmail_smtp enabled", enabled and provider == 'gmail_smtp')
        
        # 7. GET /admin/email-logs
        success, resp = self.api_call('GET', 'admin/email-logs?limit=10', 200)
        self.log_test("GET /admin/email-logs", success)
        
        # 8. GET /admin/newsletter/subscribers
        success, resp = self.api_call('GET', 'admin/newsletter/subscribers', 200)
        self.log_test("GET /admin/newsletter/subscribers", success)
        
        # 9. GET /admin/newsletter/issues
        success, resp = self.api_call('GET', 'admin/newsletter/issues', 200)
        self.log_test("GET /admin/newsletter/issues", success)
        
        # 10. GET /admin/newsletter/autosend
        success, resp = self.api_call('GET', 'admin/newsletter/autosend', 200)
        original_autosend = resp.get('enabled', True)
        self.log_test("GET /admin/newsletter/autosend", success)
        
        # 11. POST /admin/newsletter/autosend (toggle off then restore)
        success, resp = self.api_call('POST', 'admin/newsletter/autosend', 200,
            {'enabled': False})
        self.log_test("POST /admin/newsletter/autosend (disable)", success)
        
        # Restore original value
        success, resp = self.api_call('POST', 'admin/newsletter/autosend', 200,
            {'enabled': original_autosend})
        self.log_test("POST /admin/newsletter/autosend (restore)", success)
        
        # 12. GET /admin/newsletter/briefing-reminder
        success, resp = self.api_call('GET', 'admin/newsletter/briefing-reminder', 200)
        original_reminder = resp.get('enabled', True)
        self.log_test("GET /admin/newsletter/briefing-reminder", success)
        
        # 13. POST /admin/newsletter/briefing-reminder (toggle off then restore)
        success, resp = self.api_call('POST', 'admin/newsletter/briefing-reminder', 200,
            {'enabled': False})
        self.log_test("POST /admin/newsletter/briefing-reminder (disable)", success)
        
        # Restore original value
        success, resp = self.api_call('POST', 'admin/newsletter/briefing-reminder', 200,
            {'enabled': original_reminder})
        self.log_test("POST /admin/newsletter/briefing-reminder (restore)", success)
        
        # 14. GET /admin/newsletter/digest-preview
        success, resp = self.api_call('GET', 'admin/newsletter/digest-preview', 200)
        self.log_test("GET /admin/newsletter/digest-preview", success)

    # ==================== CLEANUP ====================
    
    def cleanup(self):
        """Clean up test data"""
        print("\n" + "="*60)
        print("CLEANUP: Removing test data")
        print("="*60)
        
        # Delete test posts
        for post_id in self.test_data_to_cleanup['posts']:
            success, _ = self.api_call('DELETE', f'admin/posts/{post_id}', 200)
            if success:
                print(f"✅ Deleted test post {post_id}")
            else:
                print(f"⚠️  Failed to delete test post {post_id}")
        
        # Delete test threads
        for thread_id in self.test_data_to_cleanup['threads']:
            success, _ = self.api_call('DELETE', f'community/threads/{thread_id}', 200)
            if success:
                print(f"✅ Deleted test thread {thread_id}")
            else:
                print(f"⚠️  Failed to delete test thread {thread_id}")
        
        # Delete test announcements
        for ann_id in self.test_data_to_cleanup['announcements']:
            success, _ = self.api_call('DELETE', f'community/announcements/{ann_id}', 200)
            if success:
                print(f"✅ Deleted test announcement {ann_id}")
            else:
                print(f"⚠️  Failed to delete test announcement {ann_id}")
        
        # Delete throwaway newsletter subscribers from MongoDB
        if self.test_data_to_cleanup['newsletter_emails']:
            print("\n⚠️  CRITICAL: Throwaway newsletter emails need manual cleanup from MongoDB:")
            print("   Connect to MongoDB and run:")
            emails_str = str(self.test_data_to_cleanup['newsletter_emails'])
            print("   db.newsletter_subscribers.deleteMany({email: {$in: " + emails_str + "}})")

    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("TRADING NARRATIVE - COMPREHENSIVE REGRESSION TEST")
        print("Testing refactored backend (server.py → modules)")
        print("="*60)
        
        # Run test suites
        if not self.test_auth():
            print("\n❌ Auth tests failed - stopping")
            return False
        
        self.test_posts()
        self.test_comments_bookmarks()
        self.test_billing()
        self.test_newsletter()
        self.test_analytics()
        self.test_community()
        self.test_admin()
        
        # Cleanup
        self.cleanup()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"✅ Success rate: {round(self.tests_passed * 100 / self.tests_run, 1)}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed tests ({len(self.failed_tests)}):")
            for failure in self.failed_tests:
                print(f"   - {failure}")
        else:
            print("\n✅ All tests passed!")
        
        print("="*60)
        
        return len(self.failed_tests) == 0


def main():
    tester = TradingNarrativeRegressionTest()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
