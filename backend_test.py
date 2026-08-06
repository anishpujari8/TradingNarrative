"""
Comprehensive backend API test for The Trading Narrative
Tests all endpoints using the public URL from frontend/.env
"""
import requests
import uuid
import sys
import os

# Read public URL from frontend/.env
BACKEND_URL = "https://insight-hub-484.preview.emergentagent.com"
BASE = f"{BACKEND_URL}/api"

PASS, FAIL = 0, 0
test_results = {
    "passed": [],
    "failed": []
}


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  ✅ PASS: {name}')
        test_results["passed"].append(name)
    else:
        FAIL += 1
        print(f'  ❌ FAIL: {name} {detail}')
        test_results["failed"].append({"test": name, "detail": detail})


def main():
    print('=' * 80)
    print('🧪 BACKEND API TEST: The Trading Narrative')
    print('=' * 80)
    print(f'Testing against: {BASE}\n')

    # ==================== HEALTH & SEED ====================
    print('\n📋 1. HEALTH & SEED DATA')
    try:
        r = requests.get(f'{BASE}/health', timeout=10)
        check('GET /api/health returns 200', r.status_code == 200, r.text)
    except Exception as e:
        check('GET /api/health returns 200', False, str(e))

    # ==================== POSTS (PUBLIC) ====================
    print('\n📝 2. POSTS (PUBLIC ENDPOINTS)')
    try:
        r = requests.get(f'{BASE}/posts', timeout=10)
        posts = r.json().get('posts', [])
        check('GET /api/posts returns 200', r.status_code == 200)
        check('GET /api/posts returns 12 seeded posts', len(posts) == 12, f'got {len(posts)}')
        check('POST list NEVER includes content_blocks field', all('content_blocks' not in p for p in posts))
        
        premium_posts = [p for p in posts if p['tier'] == 'premium']
        free_posts = [p for p in posts if p['tier'] == 'free']
        check('Has both premium and free posts', len(premium_posts) > 0 and len(free_posts) > 0, 
              f'premium={len(premium_posts)}, free={len(free_posts)}')
        
        if premium_posts:
            prem_slug = premium_posts[0]['slug']
            print(f'   Using premium post: {prem_slug}')
        if free_posts:
            free_slug = free_posts[0]['slug']
            print(f'   Using free post: {free_slug}')
    except Exception as e:
        check('GET /api/posts', False, str(e))
        print(f'   ⚠️  Cannot continue without posts data')
        sys.exit(1)

    # ==================== SERVER-SIDE PAYWALL ====================
    print('\n🔒 3. SERVER-SIDE PAYWALL (PREMIUM POST WITHOUT AUTH)')
    try:
        r = requests.get(f'{BASE}/posts/{prem_slug}', timeout=10)
        d = r.json()
        check('GET premium post WITHOUT auth returns 200', r.status_code == 200)
        check('Premium post is_locked=true for anon', d.get('is_locked') is True, f"is_locked={d.get('is_locked')}")
        check('Premium post shows only 3 content_blocks', len(d.get('content_blocks', [])) == 3, 
              f"got {len(d.get('content_blocks', []))} blocks")
        check('Premium post total_blocks > shown_blocks', d.get('total_blocks', 0) > d.get('shown_blocks', 0),
              f"total={d.get('total_blocks')}, shown={d.get('shown_blocks')}")
        check('Premium post has related posts', len(d.get('related', [])) > 0)
    except Exception as e:
        check('GET premium post paywall test', False, str(e))

    # Free post should be fully open
    try:
        r = requests.get(f'{BASE}/posts/{free_slug}', timeout=10)
        d = r.json()
        check('Free post is_locked=false for anon', d.get('is_locked') is False)
        check('Free post shows all content_blocks', len(d.get('content_blocks', [])) == d.get('total_blocks', 0))
    except Exception as e:
        check('GET free post test', False, str(e))

    # ==================== AUTH: REGISTER & LOGIN ====================
    print('\n🔐 4. AUTH: REGISTER & LOGIN')
    email = f'test-{uuid.uuid4().hex[:8]}@tradingnarrative.com'
    password = 'TestPass123!'
    token = None
    
    try:
        r = requests.post(f'{BASE}/auth/register', json={
            'email': email, 'password': password, 'name': 'Test User'
        }, timeout=10)
        check('POST /api/auth/register returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            token = r.json().get('token')
            user = r.json().get('user', {})
            check('Register returns token', token is not None)
            check('Register returns user with is_premium=false', user.get('is_premium') is False)
    except Exception as e:
        check('POST /api/auth/register', False, str(e))

    # Login
    try:
        r = requests.post(f'{BASE}/auth/login', json={
            'email': email, 'password': password
        }, timeout=10)
        check('POST /api/auth/login returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            token = r.json().get('token')
            check('Login returns is_premium=false for new user', r.json()['user']['is_premium'] is False)
    except Exception as e:
        check('POST /api/auth/login', False, str(e))

    if not token:
        print('   ⚠️  Cannot continue without auth token')
        sys.exit(1)

    hdr = {'Authorization': f'Bearer {token}'}

    # GET /auth/me
    try:
        r = requests.get(f'{BASE}/auth/me', headers=hdr, timeout=10)
        check('GET /api/auth/me returns 200', r.status_code == 200)
    except Exception as e:
        check('GET /api/auth/me', False, str(e))

    # ==================== MAGIC LINK ====================
    print('\n✨ 5. MAGIC LINK AUTH (MOCKED)')
    ml_email = f'magic-{uuid.uuid4().hex[:8]}@test.com'
    try:
        r = requests.post(f'{BASE}/auth/magic-link/request', json={'email': ml_email}, timeout=10)
        check('POST /api/auth/magic-link/request returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            data = r.json()
            check('Magic link response has magic_link field', 'magic_link' in data)
            check('Magic link response has dev_mode=true', data.get('dev_mode') is True)
            
            if 'magic_link' in data:
                ml_token = data['magic_link'].split('token=')[-1]
                # Verify magic link
                r2 = requests.post(f'{BASE}/auth/magic-link/verify', json={'token': ml_token}, timeout=10)
                check('POST /api/auth/magic-link/verify returns 200', r2.status_code == 200, r2.text)
                check('Magic link verify returns token', 'token' in r2.json())
                
                # Try to use same token again (should fail - single use)
                r3 = requests.post(f'{BASE}/auth/magic-link/verify', json={'token': ml_token}, timeout=10)
                check('Magic link is single-use (2nd verify fails)', r3.status_code == 400)
    except Exception as e:
        check('Magic link flow', False, str(e))

    # ==================== BILLING: CHECKOUT ====================
    print('\n💳 6. MOCK BILLING: CHECKOUT')
    try:
        r = requests.get(f'{BASE}/billing/config', timeout=10)
        check('GET /api/billing/config returns 200', r.status_code == 200)
        check('Billing config shows mock_mode=true', r.json().get('mock_mode') is True)
    except Exception as e:
        check('GET /api/billing/config', False, str(e))

    try:
        r = requests.post(f'{BASE}/billing/checkout', json={'plan': 'monthly'}, headers=hdr, timeout=10)
        check('POST /api/billing/checkout returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            data = r.json()
            check('Checkout returns subscription', 'subscription' in data)
            check('Checkout returns invoice', 'invoice' in data)
            inv = data.get('invoice', {})
            check('Invoice amount is $8.00 for monthly', inv.get('amount') == 8.0)
            check('Invoice status is paid', inv.get('status') == 'paid')
    except Exception as e:
        check('POST /api/billing/checkout', False, str(e))

    # Verify user is now premium
    try:
        r = requests.get(f'{BASE}/auth/me', headers=hdr, timeout=10)
        check('After checkout, user is_premium=true', r.json()['user']['is_premium'] is True)
    except Exception as e:
        check('Verify premium status after checkout', False, str(e))

    # ==================== PREMIUM ACCESS ====================
    print('\n🎯 7. PREMIUM USER GETS FULL CONTENT')
    try:
        r = requests.get(f'{BASE}/posts/{prem_slug}', headers=hdr, timeout=10)
        d = r.json()
        check('Premium user: is_locked=false', d.get('is_locked') is False, f"is_locked={d.get('is_locked')}")
        check('Premium user: shown_blocks == total_blocks', 
              d.get('shown_blocks') == d.get('total_blocks'),
              f"shown={d.get('shown_blocks')}, total={d.get('total_blocks')}")
    except Exception as e:
        check('Premium user full access test', False, str(e))

    # ==================== BILLING: SUBSCRIPTION & INVOICES ====================
    print('\n📊 8. BILLING: SUBSCRIPTION & INVOICES')
    try:
        r = requests.get(f'{BASE}/billing/subscription', headers=hdr, timeout=10)
        check('GET /api/billing/subscription returns 200', r.status_code == 200)
        check('Subscription endpoint returns subscription object', r.json().get('subscription') is not None)
    except Exception as e:
        check('GET /api/billing/subscription', False, str(e))

    try:
        r = requests.get(f'{BASE}/billing/invoices', headers=hdr, timeout=10)
        check('GET /api/billing/invoices returns 200', r.status_code == 200)
        invoices = r.json().get('invoices', [])
        check('Invoices list has at least 1 invoice', len(invoices) >= 1, f'got {len(invoices)}')
    except Exception as e:
        check('GET /api/billing/invoices', False, str(e))

    # ==================== BILLING: CANCEL ====================
    print('\n❌ 9. BILLING: CANCEL SUBSCRIPTION')
    try:
        r = requests.post(f'{BASE}/billing/cancel', headers=hdr, timeout=10)
        check('POST /api/billing/cancel returns 200', r.status_code == 200, r.text)
    except Exception as e:
        check('POST /api/billing/cancel', False, str(e))

    # Verify premium access revoked
    try:
        r = requests.get(f'{BASE}/posts/{prem_slug}', headers=hdr, timeout=10)
        d = r.json()
        check('After cancel: premium post is_locked=true again', d.get('is_locked') is True)
        check('After cancel: only 3 blocks shown again', len(d.get('content_blocks', [])) == 3)
    except Exception as e:
        check('Verify paywall after cancel', False, str(e))

    # ==================== NEWSLETTER ====================
    print('\n📧 10. NEWSLETTER SUBSCRIBE')
    nl_email = f'newsletter-{uuid.uuid4().hex[:8]}@test.com'
    try:
        r = requests.post(f'{BASE}/newsletter/subscribe', json={
            'email': nl_email, 'source': 'test'
        }, timeout=10)
        check('POST /api/newsletter/subscribe returns 200', r.status_code == 200, r.text)
        check('Newsletter subscribe returns ok=true', r.json().get('ok') is True)
        
        # Try to subscribe again (dedupe)
        r2 = requests.post(f'{BASE}/newsletter/subscribe', json={
            'email': nl_email, 'source': 'test'
        }, timeout=10)
        check('Newsletter dedupe: already=true on 2nd subscribe', r2.json().get('already') is True)
    except Exception as e:
        check('Newsletter subscribe flow', False, str(e))

    # ==================== SITEMAP ====================
    print('\n🗺️  11. SITEMAP')
    try:
        r = requests.get(f'{BASE}/sitemap.xml', timeout=10)
        check('GET /api/sitemap.xml returns 200', r.status_code == 200)
        check('Sitemap contains <urlset>', '<urlset' in r.text)
        check('Sitemap is XML', r.headers.get('content-type', '').startswith('application/xml'))
    except Exception as e:
        check('GET /api/sitemap.xml', False, str(e))

    # ==================== ADMIN AUTH ====================
    print('\n👑 12. ADMIN AUTH & ROUTES')
    admin_token = None
    try:
        r = requests.post(f'{BASE}/auth/login', json={
            'email': 'admin@tradingnarrative.com',
            'password': 'Admin@2025'
        }, timeout=10)
        check('Admin login returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            admin_token = r.json().get('token')
            user = r.json().get('user', {})
            check('Admin user has role=admin', user.get('role') == 'admin')
            check('Admin user is_premium=true', user.get('is_premium') is True)
    except Exception as e:
        check('Admin login', False, str(e))

    if not admin_token:
        print('   ⚠️  Cannot test admin routes without admin token')
    else:
        admin_hdr = {'Authorization': f'Bearer {admin_token}'}

        # ==================== ADMIN: POSTS ====================
        print('\n📝 13. ADMIN: POSTS CRUD')
        try:
            r = requests.get(f'{BASE}/admin/posts', headers=admin_hdr, timeout=10)
            check('GET /api/admin/posts returns 200', r.status_code == 200)
            admin_posts = r.json().get('posts', [])
            check('Admin posts list has 12 posts', len(admin_posts) == 12, f'got {len(admin_posts)}')
        except Exception as e:
            check('GET /api/admin/posts', False, str(e))

        # Create a test post
        test_post_id = None
        try:
            r = requests.post(f'{BASE}/admin/posts', json={
                'title': 'Test Post for API Testing',
                'excerpt': 'This is a test post created by the test suite.',
                'category': 'tech-business',
                'tier': 'premium',
                'cover_image': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1600',
                'content_blocks': [
                    'First paragraph of test content.',
                    'Second paragraph of test content.',
                    'Third paragraph of test content.',
                    'Fourth paragraph - premium users see this.'
                ],
                'featured': False,
                'status': 'published'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/admin/posts (create) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                test_post_id = r.json().get('id')
                test_post_slug = r.json().get('slug')
                check('Created post has id', test_post_id is not None)
                print(f'   Created test post: {test_post_slug}')
        except Exception as e:
            check('POST /api/admin/posts (create)', False, str(e))

        # Get the test post
        if test_post_id:
            try:
                r = requests.get(f'{BASE}/admin/posts/{test_post_id}', headers=admin_hdr, timeout=10)
                check('GET /api/admin/posts/{id} returns 200', r.status_code == 200)
            except Exception as e:
                check('GET /api/admin/posts/{id}', False, str(e))

            # Update the test post
            try:
                r = requests.put(f'{BASE}/admin/posts/{test_post_id}', json={
                    'title': 'Test Post UPDATED',
                    'excerpt': 'Updated excerpt.',
                    'category': 'finance',
                    'tier': 'free',
                    'cover_image': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1600',
                    'content_blocks': ['Updated content.'],
                    'featured': False,
                    'status': 'published'
                }, headers=admin_hdr, timeout=10)
                check('PUT /api/admin/posts/{id} (update) returns 200', r.status_code == 200, r.text)
            except Exception as e:
                check('PUT /api/admin/posts/{id} (update)', False, str(e))

            # Delete the test post
            try:
                r = requests.delete(f'{BASE}/admin/posts/{test_post_id}', headers=admin_hdr, timeout=10)
                check('DELETE /api/admin/posts/{id} returns 200', r.status_code == 200, r.text)
            except Exception as e:
                check('DELETE /api/admin/posts/{id}', False, str(e))

        # ==================== ADMIN: ANALYTICS ====================
        print('\n📊 14. ADMIN: ANALYTICS')
        try:
            r = requests.get(f'{BASE}/admin/analytics/stats', headers=admin_hdr, timeout=10)
            check('GET /api/admin/analytics/stats returns 200', r.status_code == 200)
            stats = r.json()
            check('Stats has pageviews field', 'pageviews' in stats)
            check('Stats has newsletter_subscribers field', 'newsletter_subscribers' in stats)
            check('Stats has users field', 'users' in stats)
            check('Stats has premium_subscribers field', 'premium_subscribers' in stats)
            check('Stats has top_posts array', isinstance(stats.get('top_posts'), list))
        except Exception as e:
            check('GET /api/admin/analytics/stats', False, str(e))

        # ==================== ADMIN: NEWSLETTER ====================
        print('\n📧 15. ADMIN: NEWSLETTER')
        try:
            r = requests.get(f'{BASE}/admin/newsletter/subscribers', headers=admin_hdr, timeout=10)
            check('GET /api/admin/newsletter/subscribers returns 200', r.status_code == 200)
            check('Subscribers response has total field', 'total' in r.json())
        except Exception as e:
            check('GET /api/admin/newsletter/subscribers', False, str(e))

        try:
            r = requests.get(f'{BASE}/admin/newsletter/issues', headers=admin_hdr, timeout=10)
            check('GET /api/admin/newsletter/issues returns 200', r.status_code == 200)
        except Exception as e:
            check('GET /api/admin/newsletter/issues', False, str(e))

        # Send a test issue (if we have posts and subscribers)
        if admin_posts and len(admin_posts) > 0:
            try:
                first_post_id = admin_posts[0]['id']
                r = requests.post(f'{BASE}/admin/newsletter/issues', json={
                    'post_id': first_post_id,
                    'subject': 'Test Newsletter Issue'
                }, headers=admin_hdr, timeout=10)
                check('POST /api/admin/newsletter/issues (send) returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    check('Send issue returns recipients count', 'recipients' in r.json())
            except Exception as e:
                check('POST /api/admin/newsletter/issues', False, str(e))

        # ==================== ADMIN: EMAIL LOGS ====================
        print('\n📬 16. ADMIN: EMAIL LOGS')
        try:
            r = requests.get(f'{BASE}/admin/email-logs', headers=admin_hdr, timeout=10)
            check('GET /api/admin/email-logs returns 200', r.status_code == 200)
            logs = r.json().get('logs', [])
            check('Email logs array returned', isinstance(logs, list))
            print(f'   Found {len(logs)} email logs')
        except Exception as e:
            check('GET /api/admin/email-logs', False, str(e))

        # ==================== ADMIN ROUTE PROTECTION ====================
        print('\n🔒 17. ADMIN ROUTE PROTECTION')
        try:
            r = requests.get(f'{BASE}/admin/posts', headers=hdr, timeout=10)
            check('Non-admin user blocked from /api/admin/posts (403)', r.status_code == 403)
        except Exception as e:
            check('Admin route protection', False, str(e))

    # ==================== CATEGORIES ====================
    print('\n🏷️  18. CATEGORIES')
    try:
        r = requests.get(f'{BASE}/categories', timeout=10)
        check('GET /api/categories returns 200', r.status_code == 200)
        cats = r.json()
        check('Categories returns 4 categories', len(cats) == 4, f'got {len(cats)}')
        check('Each category has slug, label, count', all('slug' in c and 'label' in c and 'count' in c for c in cats))
    except Exception as e:
        check('GET /api/categories', False, str(e))

    # ==================== SUMMARY ====================
    print('\n' + '=' * 80)
    print(f'📊 TEST SUMMARY')
    print('=' * 80)
    print(f'✅ PASSED: {PASS}')
    print(f'❌ FAILED: {FAIL}')
    print(f'📈 SUCCESS RATE: {PASS}/{PASS+FAIL} ({100*PASS/(PASS+FAIL):.1f}%)')
    print('=' * 80)

    if FAIL > 0:
        print('\n❌ FAILED TESTS:')
        for item in test_results["failed"]:
            print(f'   • {item["test"]}')
            if item["detail"]:
                print(f'     {item["detail"]}')

    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
