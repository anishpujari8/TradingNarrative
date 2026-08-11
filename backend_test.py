"""Backend API tests for audio micro-paywall, reading streaks and admin notifications."""
import requests
import sys
import uuid
from datetime import datetime, timedelta
import time

BASE_URL = "https://insight-hub-484.preview.emergentagent.com"

# Test essay slugs
GATED_ESSAY = 'the-boring-portfolio-that-beats-your-broker'
NEWSLETTER_EDITION = 'five-things-commodity-desks-need-to-know-this-week'
SHIPPING_ESSAY = 'the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a'

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.token = None
        self.user_id = None
        self.test_email = None
        self.failures = []

    def log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def test(self, name, func):
        """Run a single test"""
        self.tests_run += 1
        self.log(f"\n{'='*60}")
        self.log(f"Test {self.tests_run}: {name}")
        self.log('='*60)
        try:
            func()
            self.tests_passed += 1
            self.log(f"✅ PASSED: {name}", "SUCCESS")
            return True
        except AssertionError as e:
            self.tests_failed += 1
            self.failures.append(f"{name}: {str(e)}")
            self.log(f"❌ FAILED: {name} - {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.tests_failed += 1
            self.failures.append(f"{name}: {str(e)}")
            self.log(f"❌ ERROR: {name} - {str(e)}", "ERROR")
            return False

    def api_call(self, method, endpoint, data=None, expected_status=None, auth=True):
        """Make an API call"""
        url = f"{BASE_URL}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.log(f"{method} {endpoint}")
        if data:
            self.log(f"Request body: {data}")

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        self.log(f"Response status: {response.status_code}")
        try:
            resp_json = response.json()
            self.log(f"Response body: {resp_json}")
        except:
            resp_json = None
            self.log(f"Response text: {response.text[:200]}")

        if expected_status and response.status_code != expected_status:
            raise AssertionError(f"Expected status {expected_status}, got {response.status_code}")

        return response, resp_json

    def setup_test_user(self):
        """Create a test user and login"""
        self.test_email = f"test_streak_{uuid.uuid4().hex[:8]}@test.com"
        self.log(f"Creating test user: {self.test_email}")
        
        response, data = self.api_call(
            'POST', 'auth/register',
            data={
                'email': self.test_email,
                'password': 'Test123!',
                'name': 'Test User'
            },
            expected_status=200,
            auth=False
        )
        
        self.token = data['token']
        self.user_id = data['user']['id']
        self.log(f"User created with ID: {self.user_id}")
        return data['user']

    def test_streak_first_read(self):
        """Test first read returns extended=true, current_streak=1"""
        response, data = self.api_call(
            'POST', 'users/streak/read',
            data={'tz_offset_minutes': -330, 'slug': 'test-article-1'},
            expected_status=200
        )
        
        assert data['ok'] == True, "Response should have ok=True"
        assert data['extended'] == True, "First read should extend streak"
        assert data['current_streak'] == 1, f"Current streak should be 1, got {data['current_streak']}"
        assert data['longest_streak'] == 1, f"Longest streak should be 1, got {data['longest_streak']}"
        assert 'last_read_date' in data, "Should return last_read_date"

    def test_streak_same_day_idempotent(self):
        """Test second read same day returns extended=false (idempotent)"""
        response, data = self.api_call(
            'POST', 'users/streak/read',
            data={'tz_offset_minutes': -330, 'slug': 'test-article-2'},
            expected_status=200
        )
        
        assert data['ok'] == True, "Response should have ok=True"
        assert data['extended'] == False, "Same day read should not extend streak"
        assert data['current_streak'] == 1, f"Current streak should still be 1, got {data['current_streak']}"

    def test_streak_without_auth(self):
        """Test POST /api/users/streak/read without auth returns 401"""
        old_token = self.token
        self.token = None
        
        response, data = self.api_call(
            'POST', 'users/streak/read',
            data={'tz_offset_minutes': -330, 'slug': 'test-article'},
            expected_status=401,
            auth=False
        )
        
        self.token = old_token

    def test_auth_me_includes_streak_fields(self):
        """Test GET /api/auth/me includes current_streak, longest_streak, last_read_date"""
        response, data = self.api_call(
            'GET', 'auth/me',
            expected_status=200
        )
        
        user = data['user']
        assert 'current_streak' in user, "User should have current_streak field"
        assert 'longest_streak' in user, "User should have longest_streak field"
        assert 'last_read_date' in user, "User should have last_read_date field"
        self.log(f"Streak fields: current={user['current_streak']}, longest={user['longest_streak']}, last_read={user['last_read_date']}")

    def test_regression_register(self):
        """Test /api/auth/register still works"""
        test_email = f"test_reg_{uuid.uuid4().hex[:8]}@test.com"
        response, data = self.api_call(
            'POST', 'auth/register',
            data={
                'email': test_email,
                'password': 'Test123!',
                'name': 'Regression Test'
            },
            expected_status=200,
            auth=False
        )
        assert 'token' in data, "Should return token"
        assert 'user' in data, "Should return user"

    def test_regression_login(self):
        """Test /api/auth/login still works"""
        response, data = self.api_call(
            'POST', 'auth/login',
            data={
                'email': self.test_email,
                'password': 'Test123!'
            },
            expected_status=200,
            auth=False
        )
        assert 'token' in data, "Should return token"
        assert 'user' in data, "Should return user"

    def test_regression_get_posts(self):
        """Test GET /api/posts still works"""
        response, data = self.api_call(
            'GET', 'posts',
            expected_status=200,
            auth=False
        )
        assert 'posts' in data, "Should return posts array"

    def test_regression_get_specific_post(self):
        """Test GET /api/posts/insight-hub-484 still works"""
        response, data = self.api_call(
            'GET', 'posts/insight-hub-484',
            expected_status=200,
            auth=False
        )
        assert 'slug' in data, "Should return post data"

    def test_newsletter_subscribe_admin_alert(self):
        """Test admin alert on newsletter subscribe (ONLY ONCE)"""
        test_email = f"test_newsletter_{uuid.uuid4().hex[:8]}@test.com"
        self.log(f"⚠️  SENDING REAL EMAIL to admin for newsletter subscribe test with {test_email}")
        
        response, data = self.api_call(
            'POST', 'newsletter/subscribe',
            data={
                'email': test_email,
                'source': 'test'
            },
            expected_status=200,
            auth=False
        )
        
        assert data['ok'] == True, "Newsletter subscribe should succeed"
        self.log("✅ Newsletter subscribe succeeded. Checking email_logs in database...")
        
        # Give it a moment for the email to be logged
        time.sleep(2)
        
        # We can't directly check the database from here, but we can verify the response
        # The main agent should manually verify the email_logs collection
        self.log("⚠️  MANUAL VERIFICATION NEEDED: Check db.email_logs for entry with:")
        self.log(f"   - to='anishpujari8@gmail.com'")
        self.log(f"   - subject='tradingnarrative email subscriber'")
        self.log(f"   - kind='admin_subscriber_alert'")
        self.log(f"   - body contains '{test_email}'")

    # ==================== AUDIO MICRO-PAYWALL TESTS ====================
    
    def test_audio_access_anonymous_gated(self):
        """Test anonymous access to gated essay audio -> requires_signin=true, unlockable=true, scope='clip'"""
        old_token = self.token
        self.token = None
        
        response, data = self.api_call(
            'GET', f'posts/{GATED_ESSAY}/audio/access',
            expected_status=200,
            auth=False
        )
        
        assert data['requires_signin'] == True, f"Should require signin, got {data.get('requires_signin')}"
        assert data['unlockable'] == True, f"Should be unlockable, got {data.get('unlockable')}"
        assert data['scope'] == 'clip', f"Should be clip scope, got {data.get('scope')}"
        assert data['price_inr'] == 45.0, f"Price INR should be 45.0, got {data.get('price_inr')}"
        assert data['price_usd'] == 0.5, f"Price USD should be 0.5, got {data.get('price_usd')}"
        
        self.token = old_token

    def test_audio_access_newsletter_edition(self):
        """Test newsletter edition audio access -> free_audio=true, scope='full', unlockable=false"""
        response, data = self.api_call(
            'GET', f'posts/{NEWSLETTER_EDITION}/audio/access',
            expected_status=200
        )
        
        assert data['free_audio'] == True, f"Should have free audio, got {data.get('free_audio')}"
        assert data['scope'] == 'full', f"Should be full scope, got {data.get('scope')}"
        assert data['unlockable'] == False, f"Should not be unlockable (already free), got {data.get('unlockable')}"

    def test_audio_access_shipping_essay(self):
        """Test shipping essay audio access -> free_audio=true, scope='full'"""
        response, data = self.api_call(
            'GET', f'posts/{SHIPPING_ESSAY}/audio/access',
            expected_status=200
        )
        
        assert data['free_audio'] == True, f"Should have free audio, got {data.get('free_audio')}"
        assert data['scope'] == 'full', f"Should be full scope, got {data.get('scope')}"

    def test_audio_stream_anonymous_401(self):
        """Test anonymous GET /api/posts/{slug}/audio -> 401"""
        old_token = self.token
        self.token = None
        
        response, data = self.api_call(
            'GET', f'posts/{GATED_ESSAY}/audio?voice=male',
            expected_status=401,
            auth=False
        )
        
        self.token = old_token

    def test_audio_stream_free_user_clip(self):
        """Test free user gets clip scope on gated essay"""
        url = f"{BASE_URL}/api/posts/{GATED_ESSAY}/audio?voice=male"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        self.log(f"GET {url}")
        response = requests.get(url, headers=headers)
        
        self.log(f"Response status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        scope = response.headers.get('X-Audio-Scope')
        self.log(f"X-Audio-Scope header: {scope}")
        assert scope == 'clip', f"Expected clip scope, got {scope}"
        
        content_length = len(response.content)
        self.log(f"Audio content length: {content_length} bytes (~{content_length/1024:.1f} KB)")
        # 20s clip at 64kbps ≈ 160KB, allow some variance
        assert 100000 < content_length < 250000, f"Clip should be ~160KB, got {content_length/1024:.1f}KB"

    def test_audio_stream_free_user_full_shipping(self):
        """Test free user gets full scope on shipping essay"""
        url = f"{BASE_URL}/api/posts/{SHIPPING_ESSAY}/audio?voice=male"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        self.log(f"GET {url}")
        response = requests.get(url, headers=headers, timeout=60)
        
        self.log(f"Response status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        scope = response.headers.get('X-Audio-Scope')
        self.log(f"X-Audio-Scope header: {scope}")
        assert scope == 'full', f"Expected full scope, got {scope}"
        
        content_length = len(response.content)
        self.log(f"Audio content length: {content_length} bytes (~{content_length/1024:.1f} KB)")
        # Full narration should be significantly larger than clip
        assert content_length > 250000, f"Full audio should be >250KB, got {content_length/1024:.1f}KB"

    def test_audio_razorpay_checkout(self):
        """Test Razorpay checkout creation for audio unlock -> amount=4500 paise, currency INR"""
        response, data = self.api_call(
            'POST', 'billing/audio/razorpay/checkout',
            data={'slug': GATED_ESSAY},
            expected_status=200
        )
        
        assert data['ok'] == True, "Should return ok=True"
        assert data['amount'] == 4500, f"Amount should be 4500 paise, got {data.get('amount')}"
        assert data['currency'] == 'INR', f"Currency should be INR, got {data.get('currency')}"
        assert 'order_id' in data or 'ref_id' in data, "Should return order_id or ref_id"
        self.log(f"Razorpay order created: {data.get('order_id') or data.get('ref_id')}")

    def test_audio_stripe_checkout(self):
        """Test Stripe checkout creation for audio unlock -> checkout_url + session_id"""
        response, data = self.api_call(
            'POST', 'billing/audio/checkout',
            data={'slug': GATED_ESSAY, 'origin_url': BASE_URL},
            expected_status=200
        )
        
        assert data['ok'] == True, "Should return ok=True"
        if not data.get('mock'):
            assert 'checkout_url' in data, "Should return checkout_url"
            assert 'session_id' in data, "Should return session_id"
            self.log(f"Stripe session created: {data.get('session_id')}")
        else:
            self.log("Mock mode: checkout created without real Stripe session")

    def test_audio_negative_buy_free_essay(self):
        """Test buying a free-audio essay (shipping) returns 400"""
        response, data = self.api_call(
            'POST', 'billing/audio/razorpay/checkout',
            data={'slug': SHIPPING_ESSAY},
            expected_status=400
        )
        
        self.log(f"Expected 400 error: {data}")

    def test_audio_negative_invalid_slug(self):
        """Test buying with invalid slug returns 404"""
        response, data = self.api_call(
            'POST', 'billing/audio/razorpay/checkout',
            data={'slug': 'nonexistent-essay-slug-12345'},
            expected_status=404
        )
        
        self.log(f"Expected 404 error: {data}")

    def test_audio_fulfillment_flow(self):
        """Test fulfillment: simulate payment, verify purchased_audio_slugs, check access"""
        # Create a fresh user for this test
        fresh_email = f"test_audio_fulfill_{uuid.uuid4().hex[:8]}@test.com"
        self.log(f"Creating fresh user for fulfillment test: {fresh_email}")
        
        response, data = self.api_call(
            'POST', 'auth/register',
            data={'email': fresh_email, 'password': 'Test123!', 'name': 'Audio Test'},
            expected_status=200,
            auth=False
        )
        
        fresh_token = data['token']
        fresh_user_id = data['user']['id']
        
        # Create Razorpay order
        old_token = self.token
        self.token = fresh_token
        
        response, order_data = self.api_call(
            'POST', 'billing/audio/razorpay/checkout',
            data={'slug': GATED_ESSAY},
            expected_status=200
        )
        
        order_id = order_data.get('order_id') or order_data.get('ref_id')
        self.log(f"Order created: {order_id}")
        
        # Simulate payment verification (mock mode will grant access immediately)
        response, verify_data = self.api_call(
            'POST', 'billing/razorpay/verify',
            data={
                'order_id': order_id,
                'payment_id': f'pay_mock_{uuid.uuid4().hex[:14]}',
                'signature': 'mock_signature'
            },
            expected_status=200
        )
        
        assert verify_data['ok'] == True, "Verification should succeed"
        self.log("Payment verified successfully")
        
        # Check access endpoint now shows purchased=true, scope='full'
        response, access_data = self.api_call(
            'GET', f'posts/{GATED_ESSAY}/audio/access',
            expected_status=200
        )
        
        assert access_data['purchased'] == True, f"Should show purchased=true, got {access_data.get('purchased')}"
        assert access_data['scope'] == 'full', f"Should show full scope, got {access_data.get('scope')}"
        self.log("✅ Access endpoint confirms purchase")
        
        # Check audio stream now returns full scope
        url = f"{BASE_URL}/api/posts/{GATED_ESSAY}/audio?voice=male"
        headers = {'Authorization': f'Bearer {fresh_token}'}
        audio_response = requests.get(url, headers=headers, timeout=60)
        
        assert audio_response.status_code == 200, f"Audio stream should work, got {audio_response.status_code}"
        scope = audio_response.headers.get('X-Audio-Scope')
        assert scope == 'full', f"Audio should be full scope, got {scope}"
        self.log("✅ Audio stream returns full scope")
        
        # Try to buy again -> should return 400 "already own"
        response, rebuy_data = self.api_call(
            'POST', 'billing/audio/razorpay/checkout',
            data={'slug': GATED_ESSAY},
            expected_status=400
        )
        self.log(f"✅ Re-buying returns 400: {rebuy_data.get('detail')}")
        
        self.token = old_token

    def test_regression_subscription_checkout(self):
        """Test subscription checkout still works -> POST /api/billing/razorpay/checkout {plan:'monthly'}"""
        # Create a fresh user for subscription test
        sub_email = f"test_sub_{uuid.uuid4().hex[:8]}@test.com"
        response, data = self.api_call(
            'POST', 'auth/register',
            data={'email': sub_email, 'password': 'Test123!', 'name': 'Sub Test'},
            expected_status=200,
            auth=False
        )
        
        sub_token = data['token']
        old_token = self.token
        self.token = sub_token
        
        response, checkout_data = self.api_call(
            'POST', 'billing/razorpay/checkout',
            data={'plan': 'monthly'},
            expected_status=200
        )
        
        assert checkout_data['ok'] == True, "Checkout should succeed"
        assert checkout_data['amount'] == 9900, f"Monthly plan should be 9900 paise, got {checkout_data.get('amount')}"
        assert checkout_data['currency'] == 'INR', f"Currency should be INR, got {checkout_data.get('currency')}"
        self.log("✅ Subscription checkout still works")
        
        self.token = old_token

    def summary(self):
        """Print test summary"""
        self.log("\n" + "="*60)
        self.log("TEST SUMMARY")
        self.log("="*60)
        self.log(f"Total tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {self.tests_failed}")
        
        if self.failures:
            self.log("\nFailed tests:")
            for failure in self.failures:
                self.log(f"  - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"\nSuccess rate: {success_rate:.1f}%")
        
        return self.tests_failed == 0


def main():
    runner = TestRunner()
    
    try:
        # Setup
        runner.log("Setting up test user...")
        runner.setup_test_user()
        
        # ==================== AUDIO MICRO-PAYWALL TESTS ====================
        runner.log("\n" + "="*60)
        runner.log("AUDIO MICRO-PAYWALL TESTS")
        runner.log("="*60)
        
        runner.test("Audio access - anonymous gated essay", runner.test_audio_access_anonymous_gated)
        runner.test("Audio access - newsletter edition (free)", runner.test_audio_access_newsletter_edition)
        runner.test("Audio access - shipping essay (free)", runner.test_audio_access_shipping_essay)
        runner.test("Audio stream - anonymous returns 401", runner.test_audio_stream_anonymous_401)
        runner.test("Audio stream - free user gets clip on gated", runner.test_audio_stream_free_user_clip)
        runner.test("Audio stream - free user gets full on shipping", runner.test_audio_stream_free_user_full_shipping)
        runner.test("Audio Razorpay checkout creation", runner.test_audio_razorpay_checkout)
        runner.test("Audio Stripe checkout creation", runner.test_audio_stripe_checkout)
        runner.test("Audio negative - buy free essay returns 400", runner.test_audio_negative_buy_free_essay)
        runner.test("Audio negative - invalid slug returns 404", runner.test_audio_negative_invalid_slug)
        runner.test("Audio fulfillment flow (purchase -> unlock)", runner.test_audio_fulfillment_flow)
        runner.test("Regression - subscription checkout works", runner.test_regression_subscription_checkout)
        
        # Reading streak tests
        runner.log("\n" + "="*60)
        runner.log("READING STREAK TESTS")
        runner.log("="*60)
        
        runner.test("First read extends streak", runner.test_streak_first_read)
        runner.test("Same day read is idempotent", runner.test_streak_same_day_idempotent)
        runner.test("Streak endpoint requires auth", runner.test_streak_without_auth)
        runner.test("Auth me includes streak fields", runner.test_auth_me_includes_streak_fields)
        
        # Regression tests
        runner.log("\n" + "="*60)
        runner.log("REGRESSION TESTS")
        runner.log("="*60)
        
        runner.test("Register endpoint works", runner.test_regression_register)
        runner.test("Login endpoint works", runner.test_regression_login)
        runner.test("Get posts works", runner.test_regression_get_posts)
        runner.test("Get specific post works", runner.test_regression_get_specific_post)
        
    except Exception as e:
        runner.log(f"Fatal error: {str(e)}", "ERROR")
        return 1
    
    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
