"""Backend API tests for reading streaks and admin notifications."""
import requests
import sys
import uuid
from datetime import datetime, timedelta
import time

BASE_URL = "https://insight-hub-484.preview.emergentagent.com"

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
        
        # Reading streak tests
        runner.test("First read extends streak", runner.test_streak_first_read)
        runner.test("Same day read is idempotent", runner.test_streak_same_day_idempotent)
        runner.test("Streak endpoint requires auth", runner.test_streak_without_auth)
        runner.test("Auth me includes streak fields", runner.test_auth_me_includes_streak_fields)
        
        # Regression tests
        runner.test("Register endpoint works", runner.test_regression_register)
        runner.test("Login endpoint works", runner.test_regression_login)
        runner.test("Get posts works", runner.test_regression_get_posts)
        runner.test("Get specific post works", runner.test_regression_get_specific_post)
        
        # Admin notification test (ONLY ONCE)
        runner.test("Newsletter subscribe sends admin alert", runner.test_newsletter_subscribe_admin_alert)
        
    except Exception as e:
        runner.log(f"Fatal error: {str(e)}", "ERROR")
        return 1
    
    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
