"""Test ElevenLabs TTS audio narration feature"""
import requests
import sys

class AudioNarrationTester:
    def __init__(self, base_url="https://insight-hub-484.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, params=None, headers=None, check_headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        req_headers = {}
        if headers:
            req_headers.update(headers)
        if self.admin_token and 'Authorization' not in req_headers:
            req_headers['Authorization'] = f'Bearer {self.admin_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, params=params, timeout=30)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check response headers if specified
                if check_headers:
                    for header_name, expected_value in check_headers.items():
                        actual_value = response.headers.get(header_name)
                        if expected_value is None:
                            # Just check if header exists
                            if actual_value:
                                print(f"   ✅ Header '{header_name}': {actual_value}")
                            else:
                                print(f"   ⚠️  Header '{header_name}' not found")
                                self.failed_tests.append(f"{name}: Missing header '{header_name}'")
                        else:
                            # Check exact value
                            if actual_value == expected_value:
                                print(f"   ✅ Header '{header_name}': {actual_value}")
                            else:
                                print(f"   ⚠️  Header '{header_name}': expected '{expected_value}', got '{actual_value}'")
                                self.failed_tests.append(f"{name}: Header '{header_name}' mismatch")
                
                # Return response for further checks
                try:
                    return success, response.json(), response
                except:
                    return success, None, response
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.json()}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, None, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, None, None

    def test_admin_login(self):
        """Test admin login and get token"""
        print("\n" + "="*60)
        print("TESTING: Admin Authentication")
        print("="*60)
        success, response, _ = self.run_test(
            "Admin Login",
            "GET",
            "auth/login",
            200,
            headers={"Content-Type": "application/json"}
        )
        # Use POST for login
        url = f"{self.base_url}/auth/login"
        try:
            response = requests.post(url, json={"email": "admin@tradingnarrative.com", "password": "Admin@2025"}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    self.admin_token = data['token']
                    print(f"✅ Admin token obtained: {self.admin_token[:20]}...")
                    self.tests_passed += 1
                    return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            self.failed_tests.append(f"Admin Login: {e}")
        self.tests_run += 1
        return False

    def test_audio_voices(self):
        """Test GET /api/audio/voices"""
        print("\n" + "="*60)
        print("TESTING: Audio Voices Endpoint")
        print("="*60)
        success, response, _ = self.run_test(
            "GET /api/audio/voices",
            "GET",
            "audio/voices",
            200,
            headers={'Authorization': ''}  # No auth needed
        )
        
        if success and response:
            enabled = response.get('enabled')
            voices = response.get('voices', [])
            
            print(f"   Enabled: {enabled}")
            print(f"   Voices count: {len(voices)}")
            
            if enabled == True:
                print("   ✅ TTS is enabled")
            else:
                print("   ❌ TTS is not enabled")
                self.failed_tests.append("Audio Voices: TTS not enabled")
            
            if len(voices) == 3:
                print("   ✅ 3 voices available")
                for v in voices:
                    print(f"      - {v.get('key')}: {v.get('label')}")
                
                # Check for expected voices
                voice_keys = [v.get('key') for v in voices]
                expected_keys = ['male', 'female', 'documentary']
                if set(voice_keys) == set(expected_keys):
                    print("   ✅ All expected voices present")
                else:
                    print(f"   ⚠️  Voice keys mismatch: {voice_keys}")
                    self.failed_tests.append(f"Audio Voices: Expected {expected_keys}, got {voice_keys}")
            else:
                print(f"   ⚠️  Expected 3 voices, got {len(voices)}")
                self.failed_tests.append(f"Audio Voices: Expected 3 voices, got {len(voices)}")
        
        return success

    def test_cached_audio_free_essay(self):
        """Test GET /api/posts/170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum/audio?voice=male"""
        print("\n" + "="*60)
        print("TESTING: Cached Audio - Free Essay (Anonymous)")
        print("="*60)
        print("⚠️  CRITICAL: Using ONLY cached combination (170-kilometres..., voice=male)")
        
        success, _, response = self.run_test(
            "GET audio for free essay (anonymous)",
            "GET",
            "posts/170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum/audio",
            200,
            params={'voice': 'male'},
            headers={'Authorization': ''},  # No auth
            check_headers={
                'X-Audio-Cache': 'hit',
                'X-Audio-Scope': 'full',
                'Content-Type': None  # Just check it exists
            }
        )
        
        if success and response:
            content_type = response.headers.get('Content-Type')
            content_length = response.headers.get('Content-Length')
            
            if content_type and 'audio/mpeg' in content_type:
                print(f"   ✅ Content-Type is audio/mpeg")
            else:
                print(f"   ⚠️  Content-Type is '{content_type}', expected 'audio/mpeg'")
                self.failed_tests.append(f"Cached Audio: Content-Type mismatch")
            
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f"   ✅ Content-Length: {content_length} bytes (~{size_mb:.2f} MB)")
                
                # Check if size is reasonable (should be ~2MB for this essay)
                if 1.5 <= size_mb <= 3.0:
                    print(f"   ✅ Audio size is reasonable for full essay")
                else:
                    print(f"   ⚠️  Audio size {size_mb:.2f} MB seems unusual (expected ~2MB)")
            
            # Check if response starts with MP3 signature
            content = response.content[:10]
            if content[:3] == b'ID3' or content[:2] == b'\xff\xfb':
                print(f"   ✅ Response begins with MP3 signature")
            else:
                print(f"   ⚠️  Response doesn't start with MP3 signature: {content[:10]}")
                self.failed_tests.append("Cached Audio: Not valid MP3 format")
        
        return success

    def test_paywall_preview_scope(self):
        """Test GET /api/posts/the-ai-infrastructure-gold-rush-who-actually-wins/audio?voice=male WITHOUT auth"""
        print("\n" + "="*60)
        print("TESTING: Paywall - Preview Scope (Anonymous)")
        print("="*60)
        print("⚠️  CRITICAL: Using ONLY cached combination (the-ai-infrastructure..., voice=male)")
        
        success, _, response = self.run_test(
            "GET audio for premium essay (anonymous)",
            "GET",
            "posts/the-ai-infrastructure-gold-rush-who-actually-wins/audio",
            200,
            params={'voice': 'male'},
            headers={'Authorization': ''},  # No auth
            check_headers={
                'X-Audio-Cache': 'hit',
                'X-Audio-Scope': 'preview'
            }
        )
        
        if success and response:
            content_length = response.headers.get('Content-Length')
            
            if content_length:
                size_kb = int(content_length) / 1024
                print(f"   ✅ Content-Length: {content_length} bytes (~{size_kb:.0f} KB)")
                
                # Check if size is reasonable for preview (should be ~439KB)
                if 300 <= size_kb <= 600:
                    print(f"   ✅ Audio size is reasonable for preview (~439KB expected)")
                else:
                    print(f"   ⚠️  Audio size {size_kb:.0f} KB seems unusual (expected ~439KB)")
        
        return success

    def test_paywall_full_scope(self):
        """Test GET /api/posts/the-ai-infrastructure-gold-rush-who-actually-wins/audio?voice=male WITH admin auth"""
        print("\n" + "="*60)
        print("TESTING: Paywall - Full Scope (Admin)")
        print("="*60)
        print("⚠️  CRITICAL: Using ONLY cached combination (the-ai-infrastructure..., voice=male)")
        
        success, _, response = self.run_test(
            "GET audio for premium essay (admin)",
            "GET",
            "posts/the-ai-infrastructure-gold-rush-who-actually-wins/audio",
            200,
            params={'voice': 'male'},
            check_headers={
                'X-Audio-Cache': 'hit',
                'X-Audio-Scope': 'full'
            }
        )
        
        if success and response:
            content_length = response.headers.get('Content-Length')
            
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f"   ✅ Content-Length: {content_length} bytes (~{size_mb:.2f} MB)")
                
                # Check if size is reasonable for full (should be ~1.3MB)
                if 1.0 <= size_mb <= 2.0:
                    print(f"   ✅ Audio size is reasonable for full essay (~1.3MB expected)")
                else:
                    print(f"   ⚠️  Audio size {size_mb:.2f} MB seems unusual (expected ~1.3MB)")
        
        return success

    def test_invalid_voice(self):
        """Test GET /api/posts/{slug}/audio?voice=alien → 400"""
        print("\n" + "="*60)
        print("TESTING: Validation - Invalid Voice")
        print("="*60)
        
        success, _, _ = self.run_test(
            "GET audio with invalid voice",
            "GET",
            "posts/170-kilometres-one-green-enfield-and-a-lesson-in-strategic-momentum/audio",
            400,
            params={'voice': 'alien'},
            headers={'Authorization': ''}
        )
        
        return success

    def test_unknown_slug(self):
        """Test GET /api/posts/unknown-slug-12345/audio?voice=male → 404"""
        print("\n" + "="*60)
        print("TESTING: Validation - Unknown Slug")
        print("="*60)
        
        success, _, _ = self.run_test(
            "GET audio with unknown slug",
            "GET",
            "posts/unknown-slug-12345/audio",
            404,
            params={'voice': 'male'},
            headers={'Authorization': ''}
        )
        
        return success


def main():
    print("\n" + "="*60)
    print("TRADING NARRATIVE - AUDIO NARRATION TESTING")
    print("ElevenLabs TTS Feature")
    print("="*60)
    
    tester = AudioNarrationTester()
    
    # Test 1: Admin Login
    if not tester.test_admin_login():
        print("\n❌ Admin login failed, stopping tests")
        return 1
    
    # Test 2: Audio Voices Endpoint
    tester.test_audio_voices()
    
    # Test 3: Cached Audio - Free Essay
    tester.test_cached_audio_free_essay()
    
    # Test 4: Paywall - Preview Scope
    tester.test_paywall_preview_scope()
    
    # Test 5: Paywall - Full Scope
    tester.test_paywall_full_scope()
    
    # Test 6: Invalid Voice
    tester.test_invalid_voice()
    
    # Test 7: Unknown Slug
    tester.test_unknown_slug()
    
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
