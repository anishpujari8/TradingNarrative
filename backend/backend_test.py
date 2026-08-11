"""Backend API tests for The Trading Narrative - Engagement Features"""
import requests
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
import os

# Backend URL from environment
BACKEND_URL = "https://insight-hub-484.preview.emergentagent.com"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

class EngagementFeaturesTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None
        self.user_id = None
        self.test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
        
        # MongoDB connection for direct data manipulation
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client['test_database']  # Use correct DB name from backend/.env
            print(f"✅ Connected to MongoDB (database: test_database)")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.db = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        if self.token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            return False, {}

    def test_early_supporters_endpoint(self):
        """Test GET /api/early-supporters (public, no auth)"""
        print("\n" + "="*60)
        print("TEST SUITE: Early Supporters Endpoint")
        print("="*60)
        
        # Test without auth (should work - public endpoint)
        success, response = self.run_test(
            "Early supporters status (public, no auth)",
            "GET",
            "early-supporters",
            200,
            headers={'Content-Type': 'application/json'}  # No auth header
        )
        
        if success:
            # Verify response structure
            if 'limit' in response and 'taken' in response and 'left' in response:
                print(f"   ✓ Response structure correct: {response}")
                if response['limit'] == 50:
                    print(f"   ✓ Limit is 50")
                    self.tests_passed += 1
                else:
                    print(f"   ✗ Limit should be 50, got {response['limit']}")
                
                if response['left'] == 50 - response['taken']:
                    print(f"   ✓ Math correct: left = {response['left']}, taken = {response['taken']}")
                    self.tests_passed += 1
                else:
                    print(f"   ✗ Math incorrect: left should be {50 - response['taken']}, got {response['left']}")
            else:
                print(f"   ✗ Response missing required fields")
        
        return success

    def register_test_user(self):
        """Register a test user"""
        print("\n" + "="*60)
        print("SETUP: Register Test User")
        print("="*60)
        
        success, response = self.run_test(
            f"Register test user ({self.test_email})",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.test_email,
                "name": "Test User",
                "password": "TestPass123!"
            },
            headers={'Content-Type': 'application/json'}  # No auth for registration
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   ✓ User registered: {self.user_id}")
            return True
        else:
            print(f"   ✗ Registration failed")
            return False

    def test_streak_milestones(self):
        """Test streak milestone logic"""
        print("\n" + "="*60)
        print("TEST SUITE: Streak Milestones")
        print("="*60)
        
        if self.db is None or not self.user_id:
            print("❌ Cannot test - MongoDB not connected or no user")
            return False
        
        # Test 1: Set streak to 6, read today -> should get milestone 7
        print("\n--- Scenario 1: Reaching 7-day milestone ---")
        yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        
        # First, verify the user exists and check its structure
        try:
            # Debug: List all users with test email pattern
            all_test_users = list(self.db.users.find({'email': {'$regex': '@test.com$'}}, {'id': 1, 'email': 1, '_id': 0}).limit(5))
            print(f"   DEBUG: Recent test users in DB: {all_test_users}")
            
            user = self.db.users.find_one({'id': self.user_id})
            if not user:
                print(f"   ✗ User not found in database with id: {self.user_id}")
                # Try finding by email
                user = self.db.users.find_one({'email': self.test_email})
                if user:
                    print(f"   ✓ Found user by email, id in DB: {user.get('id')}")
                    self.user_id = user.get('id')  # Update user_id
                else:
                    print(f"   ✗ User not found by email either: {self.test_email}")
                    return False
            print(f"   ✓ User found in DB: {user.get('email')}")
            print(f"   ✓ Current user fields: current_streak={user.get('current_streak')}, longest_streak={user.get('longest_streak')}, last_read_date={user.get('last_read_date')}")
        except Exception as e:
            print(f"   ✗ Failed to query user: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        try:
            result = self.db.users.update_one(
                {'id': self.user_id},
                {'$set': {
                    'current_streak': 6,
                    'longest_streak': 6,
                    'last_read_date': yesterday,
                    'streak_badges': []
                }}
            )
            print(f"   ✓ Set user streak: current=6, last_read={yesterday}")
            print(f"   ✓ MongoDB update matched: {result.matched_count}, modified: {result.modified_count}")
            
            # Verify the update
            user = self.db.users.find_one({'id': self.user_id})
            if user:
                print(f"   ✓ Verified in DB: current_streak={user.get('current_streak')}, last_read_date={user.get('last_read_date')}")
            else:
                print(f"   ✗ User not found after update")
        except Exception as e:
            print(f"   ✗ Failed to update user: {e}")
            return False
        
        # Call streak read endpoint
        success, response = self.run_test(
            "Read today (should reach 7-day milestone)",
            "POST",
            "users/streak/read",
            200,
            data={"tz_offset_minutes": -330}
        )
        
        if success:
            if response.get('current_streak') == 7:
                print(f"   ✓ Current streak is 7")
                self.tests_passed += 1
            else:
                print(f"   ✗ Current streak should be 7, got {response.get('current_streak')}")
            
            if response.get('milestone') == 7:
                print(f"   ✓ Milestone is 7")
                self.tests_passed += 1
            else:
                print(f"   ✗ Milestone should be 7, got {response.get('milestone')}")
            
            if 7 in response.get('streak_badges', []):
                print(f"   ✓ Badge 7 awarded")
                self.tests_passed += 1
            else:
                print(f"   ✗ Badge 7 not in badges: {response.get('streak_badges')}")
        
        # Test 2: Call again same day -> extended=false, milestone=null
        print("\n--- Scenario 2: Reading again same day (idempotent) ---")
        success, response = self.run_test(
            "Read again same day (should be idempotent)",
            "POST",
            "users/streak/read",
            200,
            data={"tz_offset_minutes": -330}
        )
        
        if success:
            if response.get('extended') == False:
                print(f"   ✓ Extended is False (idempotent)")
                self.tests_passed += 1
            else:
                print(f"   ✗ Extended should be False, got {response.get('extended')}")
            
            if response.get('milestone') is None:
                print(f"   ✓ Milestone is None (no new milestone)")
                self.tests_passed += 1
            else:
                print(f"   ✗ Milestone should be None, got {response.get('milestone')}")
            
            if 7 in response.get('streak_badges', []):
                print(f"   ✓ Badge 7 still present")
                self.tests_passed += 1
            else:
                print(f"   ✗ Badge 7 should still be present")
        
        # Test 3: Verify badges in /auth/me
        print("\n--- Scenario 3: Verify badges in /auth/me ---")
        success, response = self.run_test(
            "Get user profile (/auth/me)",
            "GET",
            "auth/me",
            200
        )
        
        if success and 'user' in response:
            user = response['user']
            if 7 in user.get('streak_badges', []):
                print(f"   ✓ Badge 7 present in /auth/me")
                self.tests_passed += 1
            else:
                print(f"   ✗ Badge 7 not in /auth/me: {user.get('streak_badges')}")
        
        return True

    def test_badge_persistence_on_reset(self):
        """Test badge persistence when streak resets"""
        print("\n" + "="*60)
        print("TEST SUITE: Badge Persistence on Reset")
        print("="*60)
        
        if self.db is None or not self.user_id:
            print("❌ Cannot test - MongoDB not connected or no user")
            return False
        
        # Set last_read_date 5 days ago with current_streak=4, longest_streak=8, badges=[7]
        five_days_ago = (datetime.utcnow() - timedelta(days=5)).date().isoformat()
        
        try:
            self.db.users.update_one(
                {'id': self.user_id},
                {'$set': {
                    'current_streak': 4,
                    'longest_streak': 8,
                    'last_read_date': five_days_ago,
                    'streak_badges': [7]
                }}
            )
            print(f"   ✓ Set user: current=4, longest=8, last_read={five_days_ago}, badges=[7]")
        except Exception as e:
            print(f"   ✗ Failed to update user: {e}")
            return False
        
        # Read today -> should reset current to 1 but keep badges
        success, response = self.run_test(
            "Read after 5-day gap (should reset streak but keep badges)",
            "POST",
            "users/streak/read",
            200,
            data={"tz_offset_minutes": -330}
        )
        
        if success:
            if response.get('current_streak') == 1:
                print(f"   ✓ Current streak reset to 1")
                self.tests_passed += 1
            else:
                print(f"   ✗ Current streak should be 1, got {response.get('current_streak')}")
            
            if response.get('longest_streak') == 8:
                print(f"   ✓ Longest streak still 8")
                self.tests_passed += 1
            else:
                print(f"   ✗ Longest streak should be 8, got {response.get('longest_streak')}")
            
            if 7 in response.get('streak_badges', []):
                print(f"   ✓ Badge 7 persisted after reset")
                self.tests_passed += 1
            else:
                print(f"   ✗ Badge 7 should persist: {response.get('streak_badges')}")
        
        return True

    def test_audio_library(self):
        """Test audio library endpoint"""
        print("\n" + "="*60)
        print("TEST SUITE: Audio Library")
        print("="*60)
        
        # Test 1: GET /api/audio/library without auth -> 401
        print("\n--- Scenario 1: Access without authentication ---")
        success, response = self.run_test(
            "GET /api/audio/library without auth (should return 401)",
            "GET",
            "audio/library",
            401,
            headers={'Content-Type': 'application/json'}  # No auth header
        )
        
        if success:
            print(f"   ✓ Correctly returns 401 for unauthenticated request")
            self.tests_passed += 1
        
        # Test 2: GET /api/audio/library with fresh user -> empty list
        print("\n--- Scenario 2: Fresh user with no purchases ---")
        success, response = self.run_test(
            "GET /api/audio/library with fresh user (should return empty items)",
            "GET",
            "audio/library",
            200
        )
        
        if success:
            if 'items' in response and response['items'] == []:
                print(f"   ✓ Returns empty items array for fresh user")
                self.tests_passed += 1
            else:
                print(f"   ✗ Expected empty items array, got: {response}")
        
        # Test 3: Add purchased_audio_slugs to user and verify library returns them
        print("\n--- Scenario 3: User with purchased narrations ---")
        if self.db is None or not self.user_id:
            print("❌ Cannot test - MongoDB not connected or no user")
            return False
        
        # Add two purchased audio slugs (newest first order expected)
        test_slugs = [
            'the-boring-portfolio-that-beats-your-broker',
            'your-first-100k-is-the-hardest-a-tactical-map'
        ]
        
        try:
            result = self.db.users.update_one(
                {'id': self.user_id},
                {'$set': {'purchased_audio_slugs': test_slugs}}
            )
            print(f"   ✓ Added purchased_audio_slugs to user: {test_slugs}")
            print(f"   ✓ MongoDB update matched: {result.matched_count}, modified: {result.modified_count}")
        except Exception as e:
            print(f"   ✗ Failed to update user: {e}")
            return False
        
        success, response = self.run_test(
            "GET /api/audio/library after adding purchases (should return 2 items newest-first)",
            "GET",
            "audio/library",
            200
        )
        
        if success:
            if 'items' in response:
                items = response['items']
                if len(items) == 2:
                    print(f"   ✓ Returns 2 items")
                    self.tests_passed += 1
                    
                    # Check newest-first order (reversed from stored order)
                    if items[0]['slug'] == 'your-first-100k-is-the-hardest-a-tactical-map':
                        print(f"   ✓ First item is newest (your-first-100k...)")
                        self.tests_passed += 1
                    else:
                        print(f"   ✗ First item should be 'your-first-100k...', got: {items[0].get('slug')}")
                    
                    if items[1]['slug'] == 'the-boring-portfolio-that-beats-your-broker':
                        print(f"   ✓ Second item is older (the-boring-portfolio...)")
                        self.tests_passed += 1
                    else:
                        print(f"   ✗ Second item should be 'the-boring-portfolio...', got: {items[1].get('slug')}")
                    
                    # Verify required fields in each item
                    required_fields = ['title', 'slug', 'category_label', 'cover_image', 'read_time']
                    for i, item in enumerate(items):
                        missing = [f for f in required_fields if f not in item]
                        if not missing:
                            print(f"   ✓ Item {i+1} has all required fields: {required_fields}")
                            self.tests_passed += 1
                        else:
                            print(f"   ✗ Item {i+1} missing fields: {missing}")
                else:
                    print(f"   ✗ Expected 2 items, got {len(items)}")
            else:
                print(f"   ✗ Response missing 'items' field: {response}")
        
        return True

    def test_regression_endpoints(self):
        """Test that existing endpoints still work"""
        print("\n" + "="*60)
        print("TEST SUITE: Regression Tests")
        print("="*60)
        
        # Test GET /api/posts
        self.run_test(
            "GET /api/posts",
            "GET",
            "posts",
            200,
            headers={'Content-Type': 'application/json'}  # Public endpoint
        )
        
        # Test GET /api/briefings
        self.run_test(
            "GET /api/briefings",
            "GET",
            "briefings",
            200,
            headers={'Content-Type': 'application/json'}  # Public endpoint
        )
        
        # Test GET /api/auth/me (with auth)
        self.run_test(
            "GET /api/auth/me",
            "GET",
            "auth/me",
            200
        )
        
        # Test GET /api/billing/config
        self.run_test(
            "GET /api/billing/config",
            "GET",
            "billing/config",
            200,
            headers={'Content-Type': 'application/json'}  # Public endpoint
        )

    def cleanup(self):
        """Clean up test user"""
        if self.db is not None and self.user_id:
            try:
                self.db.users.delete_one({'id': self.user_id})
                print(f"\n🧹 Cleaned up test user: {self.test_email}")
            except Exception as e:
                print(f"\n⚠️  Failed to clean up test user: {e}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("="*60)

def main():
    tester = EngagementFeaturesTester()
    
    try:
        # Test audio library endpoint
        tester.test_audio_library()
        
        # Test early supporters endpoint (public)
        tester.test_early_supporters_endpoint()
        
        # Register test user
        if not tester.register_test_user():
            print("\n❌ Cannot continue - user registration failed")
            return 1
        
        # Test audio library with authenticated user
        tester.test_audio_library()
        
        # Test streak milestones
        tester.test_streak_milestones()
        
        # Test badge persistence on reset
        tester.test_badge_persistence_on_reset()
        
        # Regression tests
        tester.test_regression_endpoints()
        
        # Print summary
        tester.print_summary()
        
        # Cleanup
        tester.cleanup()
        
        # Return exit code
        return 0 if tester.tests_passed == tester.tests_run else 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
