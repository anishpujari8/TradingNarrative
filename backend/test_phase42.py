"""Phase 42 Testing: Metered Anonymous Access + SEO Infrastructure + Hyphen Cleanup"""
import requests
import sys
import re
from datetime import datetime
from xml.etree import ElementTree as ET

BASE_URL = "https://insight-hub-484.preview.emergentagent.com/api"
FRONTEND_URL = "https://insight-hub-484.preview.emergentagent.com"

# Test essay slugs
FREE_ESSAYS = [
    "five-things-commodity-desks-need-to-know-this-week",
    "oil-s-sharp-slide-opec-completes-the-rollback-and-smelters-paying-miners",
    "the-shipping-industry-is-sitting-on-a-15-billion-problem-and-nobody-is-talking-a",
    "the-boring-portfolio-that-beats-your-broker"
]
PREMIUM_ESSAY = "the-ai-infrastructure-gold-rush-who-actually-wins"

class Phase42Tester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def log(self, msg, level="INFO"):
        prefix = "✅" if level == "PASS" else "❌" if level == "FAIL" else "🔍"
        print(f"{prefix} {msg}")

    def test(self, name, condition, details=""):
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            self.log(f"PASS: {name}", "PASS")
            if details:
                print(f"   {details}")
            return True
        else:
            self.tests_failed += 1
            self.failures.append(name)
            self.log(f"FAIL: {name}", "FAIL")
            if details:
                print(f"   {details}")
            return False

    def test_meter_anonymous_flow(self):
        """Test the full meter flow: 3 free reads, 4th locked, re-read granted"""
        print("\n" + "="*80)
        print("TEST SUITE: METER SYSTEM (Anonymous Access)")
        print("="*80)
        
        # Create a fresh session with custom User-Agent
        session = requests.Session()
        session.headers.update({
            'User-Agent': f'MeterTest-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        })
        
        # Read first 3 free essays
        for i, slug in enumerate(FREE_ESSAYS[:3], 1):
            print(f"\n--- Reading essay {i}/3: {slug} ---")
            resp = session.get(f"{BASE_URL}/posts/{slug}")
            
            self.test(
                f"Essay {i} returns 200",
                resp.status_code == 200,
                f"Status: {resp.status_code}"
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Check meter present and incrementing
                self.test(
                    f"Essay {i} has meter data",
                    data.get('meter') is not None,
                    f"Meter: {data.get('meter')}"
                )
                
                if data.get('meter'):
                    meter = data['meter']
                    self.test(
                        f"Essay {i} meter.used = {i}",
                        meter.get('used') == i,
                        f"Expected {i}, got {meter.get('used')}"
                    )
                    self.test(
                        f"Essay {i} meter.granted = True",
                        meter.get('granted') is True,
                        f"Granted: {meter.get('granted')}"
                    )
                    self.test(
                        f"Essay {i} meter.remaining = {3-i}",
                        meter.get('remaining') == 3 - i,
                        f"Expected {3-i}, got {meter.get('remaining')}"
                    )
                
                # Check full content available
                self.test(
                    f"Essay {i} is not locked",
                    data.get('is_locked') is False,
                    f"is_locked: {data.get('is_locked')}"
                )
                
                # Check Set-Cookie header
                self.test(
                    f"Essay {i} sets fv_slugs cookie",
                    'fv_slugs' in resp.cookies or 'set-cookie' in resp.headers,
                    f"Cookies: {resp.cookies}"
                )
        
        # Read 4th free essay - should be locked with meter reason
        print(f"\n--- Reading essay 4/4 (should be locked): {FREE_ESSAYS[3]} ---")
        resp = session.get(f"{BASE_URL}/posts/{FREE_ESSAYS[3]}")
        
        self.test(
            "Essay 4 returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Essay 4 is locked",
                data.get('is_locked') is True,
                f"is_locked: {data.get('is_locked')}"
            )
            
            self.test(
                "Essay 4 lock_reason = 'meter'",
                data.get('lock_reason') == 'meter',
                f"lock_reason: {data.get('lock_reason')}"
            )
            
            # Check preview is limited (~250 words or 2 blocks)
            blocks = data.get('content_blocks', [])
            self.test(
                "Essay 4 shows preview only (≤2 blocks)",
                len(blocks) <= 2,
                f"Blocks shown: {len(blocks)}"
            )
            
            # Check word count is around 250
            total_words = sum(len(b.split()) for b in blocks)
            self.test(
                "Essay 4 preview ~250 words",
                total_words <= 300,
                f"Words shown: {total_words}"
            )
            
            # Check meter shows exhausted
            if data.get('meter'):
                meter = data['meter']
                self.test(
                    "Essay 4 meter.granted = False",
                    meter.get('granted') is False,
                    f"Granted: {meter.get('granted')}"
                )
        
        # Re-read first essay - should still be granted
        print(f"\n--- Re-reading essay 1 (should still be full): {FREE_ESSAYS[0]} ---")
        resp = session.get(f"{BASE_URL}/posts/{FREE_ESSAYS[0]}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Re-read essay 1 is not locked",
                data.get('is_locked') is False,
                f"is_locked: {data.get('is_locked')}"
            )
            
            if data.get('meter'):
                meter = data['meter']
                self.test(
                    "Re-read essay 1 meter.granted = True",
                    meter.get('granted') is True,
                    f"Granted: {meter.get('granted')}"
                )

    def test_premium_hard_lock(self):
        """Test premium essays are always locked for anonymous users"""
        print("\n" + "="*80)
        print("TEST SUITE: PREMIUM HARD LOCK")
        print("="*80)
        
        # Test with exhausted meter identity
        session1 = requests.Session()
        session1.headers.update({'User-Agent': 'MeterTest-Exhausted'})
        
        # Exhaust meter first
        for slug in FREE_ESSAYS[:3]:
            session1.get(f"{BASE_URL}/posts/{slug}")
        
        print(f"\n--- Testing premium essay with exhausted meter: {PREMIUM_ESSAY} ---")
        resp = session1.get(f"{BASE_URL}/posts/{PREMIUM_ESSAY}")
        
        self.test(
            "Premium essay returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Premium essay is locked",
                data.get('is_locked') is True,
                f"is_locked: {data.get('is_locked')}"
            )
            
            self.test(
                "Premium essay lock_reason = 'premium'",
                data.get('lock_reason') == 'premium',
                f"lock_reason: {data.get('lock_reason')}"
            )
            
            # Check preview is limited
            blocks = data.get('content_blocks', [])
            total_words = sum(len(b.split()) for b in blocks)
            self.test(
                "Premium essay preview ≤250 words",
                total_words <= 300,
                f"Words shown: {total_words}"
            )
        
        # Test with fresh meter identity
        session2 = requests.Session()
        session2.headers.update({'User-Agent': f'MeterTest-Fresh-{datetime.now().timestamp()}'})
        
        print(f"\n--- Testing premium essay with fresh meter: {PREMIUM_ESSAY} ---")
        resp = session2.get(f"{BASE_URL}/posts/{PREMIUM_ESSAY}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Premium essay locked for fresh meter",
                data.get('is_locked') is True,
                f"is_locked: {data.get('is_locked')}"
            )
            
            self.test(
                "Premium essay lock_reason = 'premium' (never metered)",
                data.get('lock_reason') == 'premium',
                f"lock_reason: {data.get('lock_reason')}"
            )

    def test_signed_in_free_user(self):
        """Test signed-in free user access"""
        print("\n" + "="*80)
        print("TEST SUITE: SIGNED-IN FREE USER")
        print("="*80)
        
        # Register a test user
        email = f"test_phase42_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
        password = "TestPass123!"
        
        print(f"\n--- Registering test user: {email} ---")
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "name": "Test User Phase42"
        })
        
        self.test(
            "User registration successful",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code != 200:
            print(f"   Registration failed: {resp.text}")
            return
        
        token = resp.json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test free essay access
        print(f"\n--- Testing free essay access: {FREE_ESSAYS[0]} ---")
        resp = requests.get(f"{BASE_URL}/posts/{FREE_ESSAYS[0]}", headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Free user can read free essay in full",
                data.get('is_locked') is False,
                f"is_locked: {data.get('is_locked')}"
            )
            
            self.test(
                "Free user has no meter",
                data.get('meter') is None,
                f"meter: {data.get('meter')}"
            )
        
        # Test premium essay access
        print(f"\n--- Testing premium essay access: {PREMIUM_ESSAY} ---")
        resp = requests.get(f"{BASE_URL}/posts/{PREMIUM_ESSAY}", headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            
            self.test(
                "Premium essay locked for free user",
                data.get('is_locked') is True,
                f"is_locked: {data.get('is_locked')}"
            )
            
            self.test(
                "Premium essay lock_reason = 'premium'",
                data.get('lock_reason') == 'premium',
                f"lock_reason: {data.get('lock_reason')}"
            )
            
            # Check 3-block preview for signed-in users
            blocks = data.get('content_blocks', [])
            self.test(
                "Premium essay shows 3-block preview for free user",
                len(blocks) == 3,
                f"Blocks shown: {len(blocks)}"
            )

    def test_seo_endpoints(self):
        """Test SEO infrastructure: RSS, sitemap, share pages"""
        print("\n" + "="*80)
        print("TEST SUITE: SEO ENDPOINTS")
        print("="*80)
        
        # Test RSS feed
        print("\n--- Testing RSS feed: /api/feed.xml ---")
        resp = requests.get(f"{BASE_URL}/feed.xml")
        
        self.test(
            "RSS feed returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            self.test(
                "RSS feed is XML",
                'xml' in resp.headers.get('content-type', '').lower(),
                f"Content-Type: {resp.headers.get('content-type')}"
            )
            
            # Parse XML
            try:
                root = ET.fromstring(resp.content)
                items = root.findall('.//item')
                self.test(
                    "RSS feed has items",
                    len(items) > 0,
                    f"Found {len(items)} items"
                )
            except Exception as e:
                self.test("RSS feed is valid XML", False, f"Parse error: {e}")
        
        # Test sitemap
        print("\n--- Testing sitemap: /api/sitemap.xml ---")
        resp = requests.get(f"{BASE_URL}/sitemap.xml")
        
        self.test(
            "Sitemap returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            content = resp.text
            
            # Check for topic URLs
            self.test(
                "Sitemap includes /topics/finance",
                '/topics/finance' in content,
                "Found /topics/finance"
            )
            
            self.test(
                "Sitemap includes /topics/tech-business",
                '/topics/tech-business' in content,
                "Found /topics/tech-business"
            )
            
            # Check for lastmod tags
            self.test(
                "Sitemap includes <lastmod> tags",
                '<lastmod>' in content,
                "Found <lastmod> tags"
            )
        
        # Test share page for premium essay
        print(f"\n--- Testing share page for premium essay: {PREMIUM_ESSAY} ---")
        resp = requests.get(f"{BASE_URL}/share/{PREMIUM_ESSAY}")
        
        self.test(
            "Share page returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            html = resp.text
            
            # Check for JSON-LD
            self.test(
                "Share page has JSON-LD script",
                'application/ld+json' in html,
                "Found JSON-LD script tag"
            )
            
            # Check for isAccessibleForFree: false
            self.test(
                "Premium share page has isAccessibleForFree: false",
                '"isAccessibleForFree": false' in html or '"isAccessibleForFree":false' in html,
                "Found isAccessibleForFree: false"
            )
            
            # Check for hasPart with cssSelector
            self.test(
                "Premium share page has hasPart with cssSelector",
                'cssSelector' in html and 'paywalled-content' in html,
                "Found hasPart.cssSelector"
            )
        
        # Test share page for free essay
        print(f"\n--- Testing share page for free essay: {FREE_ESSAYS[0]} ---")
        resp = requests.get(f"{BASE_URL}/share/{FREE_ESSAYS[0]}")
        
        if resp.status_code == 200:
            html = resp.text
            
            self.test(
                "Free share page has isAccessibleForFree: true",
                '"isAccessibleForFree": true' in html or '"isAccessibleForFree":true' in html,
                "Found isAccessibleForFree: true"
            )

    def test_hyphen_cleanup(self):
        """Test that em-dashes have been replaced"""
        print("\n" + "="*80)
        print("TEST SUITE: HYPHEN CLEANUP")
        print("="*80)
        
        # Test a few essays for em-dashes
        test_slugs = FREE_ESSAYS[:2] + [PREMIUM_ESSAY]
        
        for slug in test_slugs:
            print(f"\n--- Checking essay: {slug} ---")
            resp = requests.get(f"{BASE_URL}/posts/{slug}")
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Check content_blocks
                blocks = data.get('content_blocks', [])
                has_em_dash = any(' — ' in block for block in blocks)
                
                self.test(
                    f"No ' — ' in content_blocks",
                    not has_em_dash,
                    f"Found em-dash: {has_em_dash}"
                )
                
                # Check excerpt
                excerpt = data.get('excerpt', '')
                self.test(
                    f"No ' — ' in excerpt",
                    ' — ' not in excerpt,
                    f"Excerpt clean: {' — ' not in excerpt}"
                )

    def test_regression(self):
        """Test regression: auth, streak, audio"""
        print("\n" + "="*80)
        print("TEST SUITE: REGRESSION TESTS")
        print("="*80)
        
        # Test auth endpoints
        print("\n--- Testing auth endpoints ---")
        
        # Register
        email = f"test_regression_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "name": "Test Regression User"
        })
        
        self.test(
            "Auth register works",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code != 200:
            return
        
        token = resp.json().get('token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # Login
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": "TestPass123!"
        })
        
        self.test(
            "Auth login works",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        # Me endpoint
        resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        self.test(
            "Auth /me works",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        # Test audio endpoint (only on five-things... with voice=male)
        print(f"\n--- Testing audio endpoint: {FREE_ESSAYS[0]} ---")
        resp = requests.get(f"{BASE_URL}/posts/{FREE_ESSAYS[0]}/audio?voice=male", headers=headers)
        
        # Expected: 200 from cache or 503 if uncached (credits exhausted)
        self.test(
            "Audio endpoint returns 200 or 503",
            resp.status_code in [200, 503],
            f"Status: {resp.status_code} (200=cached, 503=credits exhausted)"
        )
        
        if resp.status_code == 200:
            # Check it's an audio clip for free user (~160KB)
            content_length = len(resp.content)
            self.test(
                "Audio clip is ~160KB for free user",
                140000 <= content_length <= 180000,
                f"Size: {content_length} bytes"
            )

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        
        if self.failures:
            print("\nFailed tests:")
            for failure in self.failures:
                print(f"  - {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        return 0 if self.tests_failed == 0 else 1

def main():
    tester = Phase42Tester()
    
    print("="*80)
    print("PHASE 42 TESTING: Metered Access + SEO + Hyphen Cleanup")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        tester.test_meter_anonymous_flow()
        tester.test_premium_hard_lock()
        tester.test_signed_in_free_user()
        tester.test_seo_endpoints()
        tester.test_hyphen_cleanup()
        tester.test_regression()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return tester.print_summary()

if __name__ == "__main__":
    sys.exit(main())
