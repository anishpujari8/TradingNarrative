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

    # ==================== BILLING: REAL STRIPE CHECKOUT ====================
    print('\n💳 6. REAL STRIPE CHECKOUT (TEST MODE)')
    try:
        r = requests.get(f'{BASE}/billing/config', timeout=10)
        check('GET /api/billing/config returns 200', r.status_code == 200)
        check('Billing config shows mock_mode=false', r.json().get('mock_mode') is False, f"mock_mode={r.json().get('mock_mode')}")
    except Exception as e:
        check('GET /api/billing/config', False, str(e))

    session_id = None
    try:
        r = requests.post(f'{BASE}/billing/checkout', json={'plan': 'monthly', 'origin_url': BACKEND_URL}, headers=hdr, timeout=10)
        check('POST /api/billing/checkout returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            data = r.json()
            check('Checkout returns mock=false', data.get('mock') is False)
            check('Checkout returns checkout_url', 'checkout_url' in data and 'checkout.stripe.com' in data.get('checkout_url', ''))
            check('Checkout returns session_id', 'session_id' in data)
            session_id = data.get('session_id')
            print(f'   Stripe session created: {session_id}')
    except Exception as e:
        check('POST /api/billing/checkout (Stripe)', False, str(e))

    # Test payment status endpoint (unpaid session)
    if session_id:
        try:
            r = requests.get(f'{BASE}/payments/status/{session_id}', timeout=10)
            check('GET /api/payments/status/{session_id} returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Payment status is pending for unpaid session', r.json().get('payment_status') == 'pending')
        except Exception as e:
            check('GET /api/payments/status/{session_id}', False, str(e))

    # Test payment status for unknown session
    try:
        r = requests.get(f'{BASE}/payments/status/cs_test_unknown_session_id', timeout=10)
        check('GET /api/payments/status for unknown session returns 404', r.status_code == 404)
    except Exception as e:
        check('GET /api/payments/status (unknown session)', False, str(e))

    # Note: User is NOT premium yet (payment not completed)
    try:
        r = requests.get(f'{BASE}/auth/me', headers=hdr, timeout=10)
        check('Before payment, user is_premium=false', r.json()['user']['is_premium'] is False)
    except Exception as e:
        check('Verify non-premium status before payment', False, str(e))

    # ==================== PASSWORD RESET FLOW ====================
    print('\n🔑 7. PASSWORD RESET FLOW')
    reset_email = f'reset-{uuid.uuid4().hex[:8]}@test.com'
    reset_password = 'ResetPass123!'
    
    # Create a user for password reset testing
    try:
        r = requests.post(f'{BASE}/auth/register', json={
            'email': reset_email, 'password': reset_password, 'name': 'Reset Test User'
        }, timeout=10)
        check('Create user for password reset test', r.status_code == 200)
    except Exception as e:
        check('Create user for password reset', False, str(e))

    # Request password reset for existing user
    reset_token = None
    try:
        r = requests.post(f'{BASE}/auth/password-reset/request', json={'email': reset_email}, timeout=10)
        check('POST /api/auth/password-reset/request (existing user) returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            data = r.json()
            check('Password reset response has dev_mode=true', data.get('dev_mode') is True)
            check('Password reset response has reset_link', 'reset_link' in data and data['reset_link'] is not None)
            if data.get('reset_link'):
                reset_token = data['reset_link'].split('token=')[-1]
                print(f'   Reset token: {reset_token[:20]}...')
    except Exception as e:
        check('POST /api/auth/password-reset/request', False, str(e))

    # Request password reset for unknown email (no account enumeration)
    try:
        r = requests.post(f'{BASE}/auth/password-reset/request', json={'email': 'unknown-user@test.com'}, timeout=10)
        check('POST /api/auth/password-reset/request (unknown email) returns 200', r.status_code == 200)
        if r.status_code == 200:
            data = r.json()
            check('Unknown email: reset_link is None (no enumeration)', data.get('reset_link') is None)
    except Exception as e:
        check('Password reset no enumeration test', False, str(e))

    # Confirm password reset with token
    new_password = 'NewPassword456!'
    if reset_token:
        try:
            r = requests.post(f'{BASE}/auth/password-reset/confirm', json={
                'token': reset_token, 'password': new_password
            }, timeout=10)
            check('POST /api/auth/password-reset/confirm returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Password reset confirm returns token', 'token' in r.json())
                check('Password reset confirm returns user', 'user' in r.json())
        except Exception as e:
            check('POST /api/auth/password-reset/confirm', False, str(e))

        # Try to use same token again (should fail - single use)
        try:
            r = requests.post(f'{BASE}/auth/password-reset/confirm', json={
                'token': reset_token, 'password': 'AnotherPass789!'
            }, timeout=10)
            check('Password reset token is single-use (2nd confirm fails)', r.status_code == 400)
        except Exception as e:
            check('Password reset single-use test', False, str(e))

        # Verify old password no longer works
        try:
            r = requests.post(f'{BASE}/auth/login', json={
                'email': reset_email, 'password': reset_password
            }, timeout=10)
            check('Old password no longer works after reset', r.status_code == 401)
        except Exception as e:
            check('Old password rejection test', False, str(e))

        # Verify new password works
        try:
            r = requests.post(f'{BASE}/auth/login', json={
                'email': reset_email, 'password': new_password
            }, timeout=10)
            check('New password works after reset', r.status_code == 200)
        except Exception as e:
            check('New password login test', False, str(e))

    # ==================== ADMIN AUTH (NEEDED FOR COMMENTS TEST) ====================
    print('\n👑 8. ADMIN AUTH')
    admin_token = None
    admin_hdr = None
    try:
        r = requests.post(f'{BASE}/auth/login', json={
            'email': 'admin@tradingnarrative.com',
            'password': 'Admin@2025'
        }, timeout=10)
        check('Admin login returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            admin_token = r.json().get('token')
            admin_hdr = {'Authorization': f'Bearer {admin_token}'}
            user = r.json().get('user', {})
            check('Admin user has role=admin', user.get('role') == 'admin')
            check('Admin user is_premium=true (always entitled)', user.get('is_premium') is True)
    except Exception as e:
        check('Admin login', False, str(e))

    # ==================== COMMENTS (PREMIUM FEATURE) ====================
    print('\n💬 9. COMMENTS (PREMIUM MEMBERS ONLY)')
    
    # GET comments (public endpoint)
    try:
        r = requests.get(f'{BASE}/posts/{prem_slug}/comments', timeout=10)
        check('GET /api/posts/{slug}/comments (public) returns 200', r.status_code == 200)
        check('Comments response has comments array', 'comments' in r.json())
    except Exception as e:
        check('GET /api/posts/{slug}/comments', False, str(e))

    # POST comment as free user (should fail with 403)
    try:
        r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={'body': 'Test comment from free user'}, headers=hdr, timeout=10)
        check('POST comment as free user returns 403', r.status_code == 403)
    except Exception as e:
        check('POST comment as free user (403)', False, str(e))

    # POST comment as admin (always premium-entitled)
    comment_id = None
    if admin_token and admin_hdr:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={'body': 'Test comment from admin user'}, headers=admin_hdr, timeout=10)
            check('POST comment as admin returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                comment_id = r.json().get('id')
                check('Comment response has id', comment_id is not None)
                check('Comment response has user_name', 'user_name' in r.json())
                check('Comment response has is_admin=true', r.json().get('is_admin') is True)
        except Exception as e:
            check('POST comment as admin', False, str(e))

    # DELETE own comment (admin deleting their own)
    if comment_id and admin_token:
        try:
            r = requests.delete(f'{BASE}/comments/{comment_id}', headers=admin_hdr, timeout=10)
            check('DELETE own comment returns 200', r.status_code == 200, r.text)
        except Exception as e:
            check('DELETE own comment', False, str(e))

    # Create another comment as admin for testing delete permissions
    other_comment_id = None
    if admin_token:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={'body': 'Another test comment'}, headers=admin_hdr, timeout=10)
            if r.status_code == 200:
                other_comment_id = r.json().get('id')
        except Exception as e:
            pass

    # Try to delete other's comment as free user (should fail with 403)
    if other_comment_id:
        try:
            r = requests.delete(f'{BASE}/comments/{other_comment_id}', headers=hdr, timeout=10)
            check("DELETE other's comment as free user returns 403", r.status_code == 403)
        except Exception as e:
            check("DELETE other's comment (403)", False, str(e))

        # Admin can delete any comment
        try:
            r = requests.delete(f'{BASE}/comments/{other_comment_id}', headers=admin_hdr, timeout=10)
            check('Admin can delete any comment (200)', r.status_code == 200)
        except Exception as e:
            check('Admin delete any comment', False, str(e))

    # ==================== REPLY THREADS (NEW FEATURE) ====================
    print('\n💬 9b. REPLY THREADS (NESTED COMMENTS)')
    
    # Create a top-level comment as admin
    top_comment_id = None
    if admin_token and admin_hdr:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={'body': 'Top-level comment for reply test'}, headers=admin_hdr, timeout=10)
            check('Create top-level comment for reply test', r.status_code == 200, r.text)
            if r.status_code == 200:
                top_comment_id = r.json().get('id')
        except Exception as e:
            check('Create top-level comment', False, str(e))

    # Reply to the top-level comment
    reply_id = None
    if top_comment_id and admin_token:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={
                'body': 'This is a reply to the top-level comment',
                'parent_id': top_comment_id
            }, headers=admin_hdr, timeout=10)
            check('POST comment with parent_id (reply) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                reply_id = r.json().get('id')
                check('Reply has parent_id set', r.json().get('parent_id') == top_comment_id)
        except Exception as e:
            check('POST reply with parent_id', False, str(e))

    # Reply to a reply (should flatten to top-level parent)
    if reply_id and admin_token:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={
                'body': 'Reply to a reply (should flatten)',
                'parent_id': reply_id
            }, headers=admin_hdr, timeout=10)
            check('Reply to reply returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Reply to reply flattens to top-level parent', r.json().get('parent_id') == top_comment_id)
        except Exception as e:
            check('Reply to reply flattening', False, str(e))

    # Invalid parent_id should return 400
    if admin_token:
        try:
            r = requests.post(f'{BASE}/posts/{prem_slug}/comments', json={
                'body': 'Reply with invalid parent',
                'parent_id': 'invalid-parent-id-12345'
            }, headers=admin_hdr, timeout=10)
            check('Invalid parent_id returns 400', r.status_code == 400)
        except Exception as e:
            check('Invalid parent_id test', False, str(e))

    # Delete top-level comment should cascade replies
    if top_comment_id and admin_token:
        try:
            # First, get comment count before delete
            r = requests.get(f'{BASE}/posts/{prem_slug}/comments', timeout=10)
            count_before = len(r.json().get('comments', []))
            
            # Delete top-level comment
            r = requests.delete(f'{BASE}/comments/{top_comment_id}', headers=admin_hdr, timeout=10)
            check('DELETE top-level comment returns 200', r.status_code == 200)
            
            # Verify replies are also deleted (cascade)
            r = requests.get(f'{BASE}/posts/{prem_slug}/comments', timeout=10)
            count_after = len(r.json().get('comments', []))
            check('Deleting top-level comment cascades replies', count_after < count_before, 
                  f'before={count_before}, after={count_after}')
        except Exception as e:
            check('Cascade delete test', False, str(e))

    # ==================== BOOKMARKS (NEW FEATURE) ====================
    print('\n🔖 9c. BOOKMARKS (READING LIST)')
    
    # Get bookmarks (requires auth)
    try:
        r = requests.get(f'{BASE}/bookmarks', timeout=10)
        check('GET /api/bookmarks without auth returns 401', r.status_code == 401)
    except Exception as e:
        check('GET /api/bookmarks (no auth)', False, str(e))

    # Get bookmarks as authenticated user
    if token and hdr:
        try:
            r = requests.get(f'{BASE}/bookmarks', headers=hdr, timeout=10)
            check('GET /api/bookmarks with auth returns 200', r.status_code == 200, r.text)
            check('Bookmarks response has posts array', 'posts' in r.json())
            check('Bookmarks response has post_ids array', 'post_ids' in r.json())
        except Exception as e:
            check('GET /api/bookmarks', False, str(e))

    # Toggle bookmark (save a post)
    bookmark_post_id = None
    if posts and len(posts) > 0:
        bookmark_post_id = posts[0]['id']
    
    if bookmark_post_id and token and hdr:
        try:
            r = requests.post(f'{BASE}/bookmarks/toggle', json={'post_id': bookmark_post_id}, headers=hdr, timeout=10)
            check('POST /api/bookmarks/toggle (save) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Toggle returns bookmarked=true on first call', r.json().get('bookmarked') is True)
        except Exception as e:
            check('POST /api/bookmarks/toggle (save)', False, str(e))

        # Toggle again (unsave)
        try:
            r = requests.post(f'{BASE}/bookmarks/toggle', json={'post_id': bookmark_post_id}, headers=hdr, timeout=10)
            check('POST /api/bookmarks/toggle (unsave) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Toggle returns bookmarked=false on second call', r.json().get('bookmarked') is False)
        except Exception as e:
            check('POST /api/bookmarks/toggle (unsave)', False, str(e))

    # Invalid post_id should return 404
    if token and hdr:
        try:
            r = requests.post(f'{BASE}/bookmarks/toggle', json={'post_id': 'invalid-post-id-12345'}, headers=hdr, timeout=10)
            check('Toggle with invalid post_id returns 404', r.status_code == 404)
        except Exception as e:
            check('Invalid post_id bookmark test', False, str(e))

    # ==================== AUTO-RENEW BILLING CONFIG (NEW FEATURE) ====================
    print('\n💳 9d. AUTO-RENEW BILLING CONFIG')
    
    try:
        r = requests.get(f'{BASE}/billing/config', timeout=10)
        check('GET /api/billing/config returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            config = r.json()
            check('Config has mock_mode field', 'mock_mode' in config)
            check('Config has auto_renew field', 'auto_renew' in config)
            check('Config auto_renew=false (shared test key)', config.get('auto_renew') is False, 
                  f"auto_renew={config.get('auto_renew')}")
            check('Config mock_mode=false', config.get('mock_mode') is False)
            check('Config has plans array', 'plans' in config and isinstance(config['plans'], list))
    except Exception as e:
        check('GET /api/billing/config', False, str(e))

    # ==================== RECOMMENDATIONS (NEW FEATURE) ====================
    print('\n🎯 9e. RECOMMENDATIONS (RELATED BY INTEREST)')
    
    # Get recommendations without slugs and without auth (should return empty)
    try:
        r = requests.get(f'{BASE}/recommendations', timeout=10)
        check('GET /api/recommendations (no slugs, no auth) returns 200', r.status_code == 200, r.text)
        if r.status_code == 200:
            check('Recommendations without history returns empty posts', len(r.json().get('posts', [])) == 0)
            check('Recommendations without history returns empty based_on', len(r.json().get('based_on', [])) == 0)
    except Exception as e:
        check('GET /api/recommendations (empty)', False, str(e))

    # Get recommendations with finance slugs (should return finance posts)
    finance_posts = [p for p in posts if p.get('category') == 'finance']
    if len(finance_posts) >= 2:
        slug1, slug2 = finance_posts[0]['slug'], finance_posts[1]['slug']
        try:
            r = requests.get(f'{BASE}/recommendations', params={'slugs': f'{slug1},{slug2}', 'limit': 6}, timeout=10)
            check('GET /api/recommendations with finance slugs returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                recs = r.json()
                check('Recommendations response has posts array', 'posts' in recs)
                check('Recommendations response has based_on array', 'based_on' in recs)
                check('Recommendations based_on includes Finance', 'Finance' in recs.get('based_on', []), 
                      f"based_on={recs.get('based_on')}")
                # Verify returned posts exclude the input slugs
                rec_slugs = [p['slug'] for p in recs.get('posts', [])]
                check('Recommendations exclude input slugs', slug1 not in rec_slugs and slug2 not in rec_slugs)
        except Exception as e:
            check('GET /api/recommendations with slugs', False, str(e))

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

    # ==================== ADMIN ROUTES (CONTINUED) ====================
    if not admin_token:
        print('   ⚠️  Cannot test admin routes without admin token')
    else:
        # ==================== ADMIN: POSTS ====================
        print('\n📝 12. ADMIN: POSTS CRUD')
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
        print('\n📊 13. ADMIN: ANALYTICS')
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
        print('\n📧 14. ADMIN: NEWSLETTER')
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
        print('\n📬 15. ADMIN: EMAIL LOGS')
        try:
            r = requests.get(f'{BASE}/admin/email-logs', headers=admin_hdr, timeout=10)
            check('GET /api/admin/email-logs returns 200', r.status_code == 200)
            logs = r.json().get('logs', [])
            check('Email logs array returned', isinstance(logs, list))
            print(f'   Found {len(logs)} email logs')
        except Exception as e:
            check('GET /api/admin/email-logs', False, str(e))

        # ==================== ADMIN ROUTE PROTECTION ====================
        print('\n🔒 16. ADMIN ROUTE PROTECTION')
        try:
            r = requests.get(f'{BASE}/admin/posts', headers=hdr, timeout=10)
            check('Non-admin user blocked from /api/admin/posts (403)', r.status_code == 403)
        except Exception as e:
            check('Admin route protection', False, str(e))

    # ==================== CATEGORIES ====================
    print('\n🏷️  17. CATEGORIES')
    try:
        r = requests.get(f'{BASE}/categories', timeout=10)
        check('GET /api/categories returns 200', r.status_code == 200)
        cats = r.json()
        check('Categories returns 4 categories', len(cats) == 4, f'got {len(cats)}')
        check('Each category has slug, label, count', all('slug' in c and 'label' in c and 'count' in c for c in cats))
    except Exception as e:
        check('GET /api/categories', False, str(e))

    # ==================== RAZORPAY CHECKOUT (INR) ====================
    print('\n💰 18. RAZORPAY CHECKOUT (INR / UPI)')
    
    # Get billing config for Razorpay
    try:
        r = requests.get(f'{BASE}/billing/config', timeout=10)
        check('GET /api/billing/config returns 200', r.status_code == 200)
        if r.status_code == 200:
            config = r.json()
            check('Config razorpay_enabled=true', config.get('razorpay_enabled') is True, f"razorpay_enabled={config.get('razorpay_enabled')}")
            check('Config razorpay_autopay=false (expected)', config.get('razorpay_autopay') is False, f"razorpay_autopay={config.get('razorpay_autopay')}")
            check('Config razorpay_key_id present', config.get('razorpay_key_id') == 'rzp_test_TMSwcg1LODuAH4')
    except Exception as e:
        check('GET /api/billing/config (Razorpay)', False, str(e))

    # Create a fresh user for Razorpay checkout test
    rzp_email = f'rzp-{uuid.uuid4().hex[:8]}@test.com'
    rzp_password = 'RzpTest123!'
    rzp_token = None
    try:
        r = requests.post(f'{BASE}/auth/register', json={
            'email': rzp_email, 'password': rzp_password, 'name': 'Razorpay Test User'
        }, timeout=10)
        check('Create user for Razorpay test', r.status_code == 200)
        if r.status_code == 200:
            rzp_token = r.json().get('token')
    except Exception as e:
        check('Create Razorpay test user', False, str(e))

    rzp_hdr = {'Authorization': f'Bearer {rzp_token}'} if rzp_token else None

    # Test monthly plan checkout
    if rzp_token and rzp_hdr:
        try:
            r = requests.post(f'{BASE}/billing/razorpay/checkout', json={'plan': 'monthly'}, headers=rzp_hdr, timeout=10)
            check('POST /api/billing/razorpay/checkout (monthly) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                data = r.json()
                check('Razorpay checkout ok=true', data.get('ok') is True)
                check('Razorpay checkout mock=false', data.get('mock') is False)
                check('Razorpay checkout kind=order (not subscription)', data.get('kind') == 'order', f"kind={data.get('kind')}")
                check('Razorpay order_id starts with order_', data.get('order_id', '').startswith('order_'), f"order_id={data.get('order_id')}")
                check('Razorpay amount=19900 paise (₹199)', data.get('amount') == 19900, f"amount={data.get('amount')}")
                check('Razorpay currency=INR', data.get('currency') == 'INR')
                check('Razorpay razorpay_key_id present', data.get('razorpay_key_id') == 'rzp_test_TMSwcg1LODuAH4')
        except Exception as e:
            check('POST /api/billing/razorpay/checkout (monthly)', False, str(e))

    # Test annual plan checkout
    if rzp_token and rzp_hdr:
        try:
            r = requests.post(f'{BASE}/billing/razorpay/checkout', json={'plan': 'annual'}, headers=rzp_hdr, timeout=10)
            check('POST /api/billing/razorpay/checkout (annual) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                data = r.json()
                check('Razorpay annual amount=199900 paise (₹1999)', data.get('amount') == 199900, f"amount={data.get('amount')}")
        except Exception as e:
            check('POST /api/billing/razorpay/checkout (annual)', False, str(e))

    # ==================== TRAFFIC ANALYTICS ====================
    print('\n📊 19. TRAFFIC ANALYTICS')
    
    # Track a pageview with LinkedIn referrer
    try:
        r = requests.post(f'{BASE}/analytics/track', json={
            'event': 'pageview',
            'path': '/',
            'meta': {
                'first_visit': True,
                'referrer': 'https://www.linkedin.com/feed/'
            }
        }, timeout=10)
        check('POST /api/analytics/track (LinkedIn referrer) returns 200', r.status_code == 200, r.text)
    except Exception as e:
        check('POST /api/analytics/track (LinkedIn)', False, str(e))

    # Track with utm_source (should override referrer)
    try:
        r = requests.post(f'{BASE}/analytics/track', json={
            'event': 'pageview',
            'path': '/pricing',
            'meta': {
                'first_visit': True,
                'referrer': 'https://www.google.com/',
                'utm_source': 'instagram',
                'utm_campaign': 'launch'
            }
        }, timeout=10)
        check('POST /api/analytics/track (UTM override) returns 200', r.status_code == 200, r.text)
    except Exception as e:
        check('POST /api/analytics/track (UTM)', False, str(e))

    # Track internal referrer (should NOT be counted as traffic source)
    try:
        r = requests.post(f'{BASE}/analytics/track', json={
            'event': 'pageview',
            'path': '/about',
            'meta': {
                'first_visit': True,
                'referrer': 'https://insight-hub-484.preview.emergentagent.com/pricing'
            }
        }, timeout=10)
        check('POST /api/analytics/track (internal referrer) returns 200', r.status_code == 200, r.text)
    except Exception as e:
        check('POST /api/analytics/track (internal)', False, str(e))

    # Get admin traffic analytics
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/traffic', params={'days': 30}, headers=admin_hdr, timeout=10)
            check('GET /api/admin/traffic?days=30 returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                traffic = r.json()
                check('Traffic has sources array', 'sources' in traffic and isinstance(traffic['sources'], list))
                check('Traffic has top_referrers array', 'top_referrers' in traffic)
                check('Traffic has campaigns array', 'campaigns' in traffic)
                check('Traffic has total_visits', 'total_visits' in traffic)
                check('Traffic has days field', traffic.get('days') == 30)
                
                # Verify LinkedIn is in sources
                sources = [s['source'] for s in traffic.get('sources', [])]
                if 'LinkedIn' in sources:
                    print(f'   ✓ LinkedIn traffic source detected')
        except Exception as e:
            check('GET /api/admin/traffic', False, str(e))

    # ==================== COMMUNITY LOUNGE ====================
    print('\n🏠 20. COMMUNITY LOUNGE (PREMIUM MEMBERS ONLY)')
    
    # Test unauthenticated access (should return 401)
    try:
        r = requests.get(f'{BASE}/community/threads', timeout=10)
        check('GET /api/community/threads (no auth) returns 401', r.status_code == 401)
    except Exception as e:
        check('GET /api/community/threads (no auth)', False, str(e))

    # Test free user access (should return 403)
    if token and hdr:
        try:
            r = requests.get(f'{BASE}/community/threads', headers=hdr, timeout=10)
            check('GET /api/community/threads (free user) returns 403', r.status_code == 403)
        except Exception as e:
            check('GET /api/community/threads (free user)', False, str(e))

    # Test admin access (should return 200)
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/community/threads', headers=admin_hdr, timeout=10)
            check('GET /api/community/threads (admin) returns 200', r.status_code == 200, r.text)
            check('Community threads response has threads array', 'threads' in r.json())
        except Exception as e:
            check('GET /api/community/threads (admin)', False, str(e))

        try:
            r = requests.get(f'{BASE}/community/announcements', headers=admin_hdr, timeout=10)
            check('GET /api/community/announcements (admin) returns 200', r.status_code == 200, r.text)
            check('Community announcements response has announcements array', 'announcements' in r.json())
        except Exception as e:
            check('GET /api/community/announcements (admin)', False, str(e))

    # ==================== COMMUNITY: ANNOUNCEMENTS (ADMIN ONLY) ====================
    print('\n📢 21. COMMUNITY: ANNOUNCEMENTS (ADMIN ONLY)')
    
    announcement_id = None
    if admin_token and admin_hdr:
        # Create announcement
        try:
            r = requests.post(f'{BASE}/community/announcements', json={
                'title': 'Test Announcement',
                'body': 'This is a test announcement from the API test suite.'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/announcements (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                announcement_id = r.json().get('id')
                check('Announcement has id', announcement_id is not None)
                check('Announcement has author', 'author' in r.json())
        except Exception as e:
            check('POST /api/community/announcements', False, str(e))

        # Try to create announcement as free user (should fail)
        if token and hdr:
            try:
                r = requests.post(f'{BASE}/community/announcements', json={
                    'title': 'Unauthorized Announcement',
                    'body': 'This should fail.'
                }, headers=hdr, timeout=10)
                check('POST /api/community/announcements (free user) returns 403', r.status_code == 403)
            except Exception as e:
                check('POST /api/community/announcements (free user)', False, str(e))

        # Delete announcement
        if announcement_id:
            try:
                r = requests.delete(f'{BASE}/community/announcements/{announcement_id}', headers=admin_hdr, timeout=10)
                check('DELETE /api/community/announcements/{id} returns 200', r.status_code == 200, r.text)
            except Exception as e:
                check('DELETE /api/community/announcements/{id}', False, str(e))

    # ==================== COMMUNITY: THREADS & REPLIES ====================
    print('\n💬 22. COMMUNITY: THREADS & REPLIES')
    
    thread_id = None
    if admin_token and admin_hdr:
        # Create thread
        try:
            r = requests.post(f'{BASE}/community/threads', json={
                'title': 'Test Discussion Thread',
                'body': 'This is a test discussion thread created by the API test suite.'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/threads returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                thread_id = r.json().get('id')
                check('Thread has id', thread_id is not None)
                check('Thread has reply_count=0', r.json().get('reply_count') == 0)
                check('Thread has pinned=false by default', r.json().get('pinned') is False)
        except Exception as e:
            check('POST /api/community/threads', False, str(e))

        # Validation: title too short
        try:
            r = requests.post(f'{BASE}/community/threads', json={
                'title': 'AB',
                'body': 'Body text'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/threads (title <3 chars) returns 400', r.status_code == 400)
        except Exception as e:
            check('Thread title validation', False, str(e))

        # Get thread detail
        if thread_id:
            try:
                r = requests.get(f'{BASE}/community/threads/{thread_id}', headers=admin_hdr, timeout=10)
                check('GET /api/community/threads/{id} returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    check('Thread detail has thread object', 'thread' in r.json())
                    check('Thread detail has replies array', 'replies' in r.json())
            except Exception as e:
                check('GET /api/community/threads/{id}', False, str(e))

            # Post a reply
            reply_id = None
            try:
                r = requests.post(f'{BASE}/community/threads/{thread_id}/replies', json={
                    'body': 'This is a test reply to the thread.'
                }, headers=admin_hdr, timeout=10)
                check('POST /api/community/threads/{id}/replies returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    reply_id = r.json().get('id')
                    check('Reply has id', reply_id is not None)
            except Exception as e:
                check('POST /api/community/threads/{id}/replies', False, str(e))

            # Validation: empty reply body
            try:
                r = requests.post(f'{BASE}/community/threads/{thread_id}/replies', json={
                    'body': ''
                }, headers=admin_hdr, timeout=10)
                check('POST reply with empty body returns 400', r.status_code == 400)
            except Exception as e:
                check('Reply body validation', False, str(e))

            # Verify reply_count incremented
            try:
                r = requests.get(f'{BASE}/community/threads/{thread_id}', headers=admin_hdr, timeout=10)
                if r.status_code == 200:
                    check('Thread reply_count incremented to 1', r.json()['thread'].get('reply_count') == 1)
                    check('Thread detail returns 1 reply', len(r.json().get('replies', [])) == 1)
            except Exception as e:
                check('Verify reply_count increment', False, str(e))

            # Delete reply
            if reply_id:
                try:
                    r = requests.delete(f'{BASE}/community/replies/{reply_id}', headers=admin_hdr, timeout=10)
                    check('DELETE /api/community/replies/{id} returns 200', r.status_code == 200, r.text)
                except Exception as e:
                    check('DELETE /api/community/replies/{id}', False, str(e))

            # Delete thread
            try:
                r = requests.delete(f'{BASE}/community/threads/{thread_id}', headers=admin_hdr, timeout=10)
                check('DELETE /api/community/threads/{id} returns 200', r.status_code == 200, r.text)
            except Exception as e:
                check('DELETE /api/community/threads/{id}', False, str(e))

    # ==================== NEW FEATURES: ITERATION 6 ====================
    print('\n🆕 23. NEW FEATURES: LOUNGE NOTIFICATIONS, PINNED THREADS, TRAFFIC TRENDS')
    
    # Test lounge_reply notifications
    if admin_token and admin_hdr:
        # Create a premium user by inserting subscription directly
        premium_email = f'premium-{uuid.uuid4().hex[:8]}@test.com'
        premium_password = 'Premium123!'
        premium_token = None
        premium_user_id = None
        
        try:
            r = requests.post(f'{BASE}/auth/register', json={
                'email': premium_email, 'password': premium_password, 'name': 'Premium Test User'
            }, timeout=10)
            if r.status_code == 200:
                premium_token = r.json().get('token')
                premium_user_id = r.json()['user']['id']
                print(f'   Created premium test user: {premium_user_id}')
        except Exception as e:
            check('Create premium test user', False, str(e))
        
        premium_hdr = {'Authorization': f'Bearer {premium_token}'} if premium_token else None
        
        # Grant premium by inserting subscription (direct MongoDB insert would be needed, but we'll use admin to create a thread)
        # For testing, we'll create a thread as admin and reply as another premium user
        
        # Create a thread as the premium user (need to grant premium first via MongoDB)
        # Since we can't directly insert into MongoDB from here, we'll test with admin creating thread
        # and another user replying
        
        test_thread_id = None
        try:
            r = requests.post(f'{BASE}/community/threads', json={
                'title': 'Thread for Notification Test',
                'body': 'Testing lounge_reply notifications.'
            }, headers=admin_hdr, timeout=10)
            if r.status_code == 200:
                test_thread_id = r.json().get('id')
                print(f'   Created test thread: {test_thread_id}')
        except Exception as e:
            check('Create thread for notification test', False, str(e))
        
        # Note: We cannot fully test lounge_reply notifications without granting premium to the second user
        # This would require direct MongoDB access. We'll document this limitation.
        print('   ⚠️  Full lounge_reply notification test requires MongoDB access to grant premium')
        
    # Test pinned threads feature
    pin_test_thread_id = None
    if admin_token and admin_hdr:
        # Create a thread for pin testing
        try:
            r = requests.post(f'{BASE}/community/threads', json={
                'title': 'Thread for Pin Test',
                'body': 'Testing pin/unpin functionality.'
            }, headers=admin_hdr, timeout=10)
            check('Create thread for pin test returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                pin_test_thread_id = r.json().get('id')
        except Exception as e:
            check('Create thread for pin test', False, str(e))
        
        # Test admin can pin thread
        if pin_test_thread_id:
            try:
                r = requests.post(f'{BASE}/community/threads/{pin_test_thread_id}/pin', headers=admin_hdr, timeout=10)
                check('POST /api/community/threads/{id}/pin (admin) returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    check('Pin response has pinned=true', r.json().get('pinned') is True)
            except Exception as e:
                check('POST /api/community/threads/{id}/pin (admin)', False, str(e))
            
            # Test non-admin premium user gets 403
            if token and hdr:
                try:
                    r = requests.post(f'{BASE}/community/threads/{pin_test_thread_id}/pin', headers=hdr, timeout=10)
                    check('POST /api/community/threads/{id}/pin (non-admin) returns 403', r.status_code == 403)
                except Exception as e:
                    check('POST /api/community/threads/{id}/pin (non-admin)', False, str(e))
            
            # Test unpinning
            try:
                r = requests.post(f'{BASE}/community/threads/{pin_test_thread_id}/pin', headers=admin_hdr, timeout=10)
                check('POST /api/community/threads/{id}/pin (unpin) returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    check('Unpin response has pinned=false', r.json().get('pinned') is False)
            except Exception as e:
                check('POST /api/community/threads/{id}/pin (unpin)', False, str(e))
            
            # Pin it again for thread list test
            try:
                r = requests.post(f'{BASE}/community/threads/{pin_test_thread_id}/pin', headers=admin_hdr, timeout=10)
            except Exception:
                pass
            
            # Test GET /api/community/threads returns pinned threads first
            try:
                r = requests.get(f'{BASE}/community/threads', headers=admin_hdr, timeout=10)
                check('GET /api/community/threads returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    threads = r.json().get('threads', [])
                    if len(threads) > 0:
                        # Check if pinned threads appear first
                        pinned_threads = [t for t in threads if t.get('pinned')]
                        if len(pinned_threads) > 0:
                            first_pinned_idx = threads.index(pinned_threads[0])
                            first_unpinned_idx = next((i for i, t in enumerate(threads) if not t.get('pinned')), len(threads))
                            check('Pinned threads appear before unpinned threads', first_pinned_idx < first_unpinned_idx, 
                                  f'first_pinned={first_pinned_idx}, first_unpinned={first_unpinned_idx}')
            except Exception as e:
                check('GET /api/community/threads (pinned first)', False, str(e))
            
            # Clean up: delete pin test thread
            try:
                r = requests.delete(f'{BASE}/community/threads/{pin_test_thread_id}', headers=admin_hdr, timeout=10)
            except Exception:
                pass
    
    # Test traffic trends feature
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/traffic', params={'days': 30}, headers=admin_hdr, timeout=10)
            check('GET /api/admin/traffic?days=30 returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                traffic = r.json()
                check('Traffic response has trend array', 'trend' in traffic and isinstance(traffic['trend'], list))
                check('Traffic response has trend_series array', 'trend_series' in traffic and isinstance(traffic['trend_series'], list))
                
                # Verify trend structure (weekly buckets)
                if len(traffic.get('trend', [])) > 0:
                    first_row = traffic['trend'][0]
                    check('Trend row has week field', 'week' in first_row)
                    # Check that trend row has source columns
                    trend_series = traffic.get('trend_series', [])
                    if len(trend_series) > 0:
                        check('Trend row has source columns from trend_series', 
                              any(s in first_row for s in trend_series),
                              f'trend_series={trend_series}, row_keys={list(first_row.keys())}')
                
                # Verify trend_series contains top sources
                if len(traffic.get('sources', [])) > 0 and len(traffic.get('trend_series', [])) > 0:
                    top_sources = [s['source'] for s in traffic['sources'][:5]]
                    trend_series = traffic['trend_series']
                    check('trend_series contains top sources or Other', 
                          any(s in trend_series or 'Other' in trend_series for s in top_sources))
        except Exception as e:
            check('GET /api/admin/traffic (trend)', False, str(e))

    # ==================== NEW FEATURES: ITERATION 7 ====================
    print('\n🆕 24. NEW FEATURES: POST ATTRIBUTION, CSV EXPORT, AUTOSEND, THREAD LOCK')
    
    # Test 1: POST ATTRIBUTION - landing_pages in traffic response
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/traffic', params={'days': 30}, headers=admin_hdr, timeout=10)
            check('GET /api/admin/traffic includes landing_pages array', r.status_code == 200, r.text)
            if r.status_code == 200:
                traffic = r.json()
                check('Traffic response has landing_pages array', 'landing_pages' in traffic and isinstance(traffic['landing_pages'], list))
                if len(traffic.get('landing_pages', [])) > 0:
                    lp = traffic['landing_pages'][0]
                    check('Landing page has path field', 'path' in lp)
                    check('Landing page has source field', 'source' in lp)
                    check('Landing page has count field', 'count' in lp)
                    print(f'   ✓ Found {len(traffic["landing_pages"])} landing pages')
        except Exception as e:
            check('GET /api/admin/traffic (landing_pages)', False, str(e))
    
    # Test 2: CSV EXPORT
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/traffic/export', params={'days': 30}, headers=admin_hdr, timeout=10)
            check('GET /api/admin/traffic/export (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('CSV export Content-Type is text/csv', 'text/csv' in r.headers.get('content-type', ''))
                check('CSV export has Content-Disposition attachment', 'attachment' in r.headers.get('content-disposition', ''))
                csv_text = r.text
                check('CSV has header row', 'section,name,source,visits,share_pct' in csv_text)
                check('CSV has source section', 'source,' in csv_text)
                check('CSV has landing_page section', 'landing_page,' in csv_text)
                print(f'   ✓ CSV export working, {len(csv_text.splitlines())} rows')
        except Exception as e:
            check('GET /api/admin/traffic/export (admin)', False, str(e))
        
        # Test non-admin gets 403
        if token and hdr:
            try:
                r = requests.get(f'{BASE}/admin/traffic/export', params={'days': 30}, headers=hdr, timeout=10)
                check('GET /api/admin/traffic/export (non-admin) returns 403', r.status_code == 403)
            except Exception as e:
                check('GET /api/admin/traffic/export (non-admin)', False, str(e))
    
    # Test 3: WEEKLY DIGEST AUTOSEND
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/newsletter/autosend', headers=admin_hdr, timeout=10)
            check('GET /api/admin/newsletter/autosend returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                data = r.json()
                check('Autosend response has enabled field', 'enabled' in data)
                check('Autosend response has last_auto_send field', 'last_auto_send' in data)
                initial_enabled = data.get('enabled')
                print(f'   Current autosend state: enabled={initial_enabled}')
        except Exception as e:
            check('GET /api/admin/newsletter/autosend', False, str(e))
        
        # Toggle autosend OFF
        try:
            r = requests.post(f'{BASE}/admin/newsletter/autosend', json={'enabled': False}, headers=admin_hdr, timeout=10)
            check('POST /api/admin/newsletter/autosend (disable) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Autosend disabled successfully', r.json().get('enabled') is False)
        except Exception as e:
            check('POST /api/admin/newsletter/autosend (disable)', False, str(e))
        
        # Toggle autosend ON (LEAVE IT ENABLED)
        try:
            r = requests.post(f'{BASE}/admin/newsletter/autosend', json={'enabled': True}, headers=admin_hdr, timeout=10)
            check('POST /api/admin/newsletter/autosend (enable) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                check('Autosend enabled successfully', r.json().get('enabled') is True)
                print('   ✓ Autosend left ENABLED as required')
        except Exception as e:
            check('POST /api/admin/newsletter/autosend (enable)', False, str(e))
    
    # Test 4: THREAD LOCK
    lock_test_thread_id = None
    if admin_token and admin_hdr:
        # Find the existing locked thread "Thread for Notification Test"
        try:
            r = requests.get(f'{BASE}/community/threads', headers=admin_hdr, timeout=10)
            if r.status_code == 200:
                threads = r.json().get('threads', [])
                notification_thread = next((t for t in threads if t['title'] == 'Thread for Notification Test'), None)
                if notification_thread:
                    lock_test_thread_id = notification_thread['id']
                    print(f'   Found existing thread "Thread for Notification Test": {lock_test_thread_id}')
                    print(f'   Current locked state: {notification_thread.get("locked")}')
        except Exception as e:
            check('Find existing locked thread', False, str(e))
        
        # If thread doesn't exist, create one for testing
        if not lock_test_thread_id:
            try:
                r = requests.post(f'{BASE}/community/threads', json={
                    'title': 'Thread for Lock Test',
                    'body': 'Testing thread lock functionality.'
                }, headers=admin_hdr, timeout=10)
                if r.status_code == 200:
                    lock_test_thread_id = r.json().get('id')
                    print(f'   Created new thread for lock test: {lock_test_thread_id}')
            except Exception as e:
                check('Create thread for lock test', False, str(e))
        
        if lock_test_thread_id:
            # Test admin can lock thread
            try:
                r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/lock', headers=admin_hdr, timeout=10)
                check('POST /api/community/threads/{id}/lock (admin) returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    check('Lock response has locked field', 'locked' in r.json())
                    is_locked = r.json().get('locked')
                    print(f'   Thread locked state toggled to: {is_locked}')
            except Exception as e:
                check('POST /api/community/threads/{id}/lock (admin)', False, str(e))
            
            # Ensure thread is LOCKED for reply test
            try:
                r = requests.get(f'{BASE}/community/threads/{lock_test_thread_id}', headers=admin_hdr, timeout=10)
                if r.status_code == 200:
                    is_locked = r.json()['thread'].get('locked')
                    if not is_locked:
                        # Lock it
                        r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/lock', headers=admin_hdr, timeout=10)
                        print('   Locked thread for reply test')
            except Exception:
                pass
            
            # Test replying to LOCKED thread returns 403
            try:
                r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/replies', json={
                    'body': 'This reply should fail because thread is locked.'
                }, headers=admin_hdr, timeout=10)
                check('POST reply to locked thread returns 403', r.status_code == 403)
                if r.status_code == 403:
                    check('Locked thread error message is friendly', 'locked' in r.json().get('detail', '').lower())
            except Exception as e:
                check('POST reply to locked thread (403)', False, str(e))
            
            # Test non-admin premium user gets 403 on lock endpoint
            if token and hdr:
                try:
                    r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/lock', headers=hdr, timeout=10)
                    check('POST /api/community/threads/{id}/lock (non-admin) returns 403', r.status_code == 403)
                except Exception as e:
                    check('POST /api/community/threads/{id}/lock (non-admin)', False, str(e))
            
            # Unlock thread to test replies work after unlock
            try:
                r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/lock', headers=admin_hdr, timeout=10)
                if r.status_code == 200 and r.json().get('locked') is False:
                    print('   Thread unlocked for reply test')
                    # Try to reply (should work now)
                    r2 = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/replies', json={
                        'body': 'This reply should work because thread is unlocked.'
                    }, headers=admin_hdr, timeout=10)
                    check('POST reply to unlocked thread returns 200', r2.status_code == 200)
            except Exception as e:
                check('POST reply to unlocked thread', False, str(e))
            
            # LEAVE THREAD LOCKED at the end (as required)
            try:
                r = requests.get(f'{BASE}/community/threads/{lock_test_thread_id}', headers=admin_hdr, timeout=10)
                if r.status_code == 200:
                    is_locked = r.json()['thread'].get('locked')
                    if not is_locked:
                        # Lock it
                        r = requests.post(f'{BASE}/community/threads/{lock_test_thread_id}/lock', headers=admin_hdr, timeout=10)
                        print('   ✓ Thread left LOCKED as required')
                    else:
                        print('   ✓ Thread already LOCKED as required')
            except Exception:
                pass

    # ==================== NEW FEATURES: ITERATION 8 ====================
    print('\n🆕 25. NEW FEATURES: CONVERSION FUNNEL, EMAIL SENDING, MEMBER PROFILES, SCHEDULED ANNOUNCEMENTS')
    
    # Test 1: ANALYTICS TRACK WITH SID (SESSION ID)
    test_sid = f'test-session-{uuid.uuid4().hex[:8]}'
    try:
        r = requests.post(f'{BASE}/analytics/track', json={
            'event': 'pageview',
            'path': '/pricing',
            'meta': {'first_visit': True, 'referrer': 'https://www.linkedin.com/'},
            'sid': test_sid
        }, timeout=10)
        check('POST /api/analytics/track accepts sid field', r.status_code == 200, r.text)
    except Exception as e:
        check('POST /api/analytics/track with sid', False, str(e))
    
    # Track more events with same sid for funnel
    try:
        requests.post(f'{BASE}/analytics/track', json={
            'event': 'subscribe_cta_click',
            'path': '/pricing',
            'meta': {},
            'sid': test_sid
        }, timeout=10)
    except Exception:
        pass
    
    # Test 2: ADMIN FUNNEL ENDPOINT
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/funnel', params={'days': 30}, headers=admin_hdr, timeout=10)
            check('GET /api/admin/funnel?days=30 (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                funnel = r.json()
                check('Funnel response has days field', funnel.get('days') == 30)
                check('Funnel response has total_sessions field', 'total_sessions' in funnel)
                check('Funnel response has funnel array', 'funnel' in funnel and isinstance(funnel['funnel'], list))
                check('Funnel response has overall object', 'overall' in funnel)
                
                if funnel.get('total_sessions', 0) > 0:
                    overall = funnel.get('overall', {})
                    check('Funnel overall has visits', 'visits' in overall)
                    check('Funnel overall has pricing_views', 'pricing_views' in overall)
                    check('Funnel overall has checkouts_started', 'checkouts_started' in overall)
                    check('Funnel overall has conversions', 'conversions' in overall)
                    
                    if len(funnel.get('funnel', [])) > 0:
                        row = funnel['funnel'][0]
                        check('Funnel row has source', 'source' in row)
                        check('Funnel row has visits', 'visits' in row)
                        check('Funnel row has pricing_views', 'pricing_views' in row)
                        check('Funnel row has checkouts_started', 'checkouts_started' in row)
                        check('Funnel row has conversions', 'conversions' in row)
                        check('Funnel row has conversion_rate', 'conversion_rate' in row)
                        print(f'   ✓ Funnel data: {funnel["total_sessions"]} sessions, {len(funnel["funnel"])} sources')
        except Exception as e:
            check('GET /api/admin/funnel (admin)', False, str(e))
        
        # Test non-admin gets 403
        if token and hdr:
            try:
                r = requests.get(f'{BASE}/admin/funnel', params={'days': 30}, headers=hdr, timeout=10)
                check('GET /api/admin/funnel (non-admin) returns 403', r.status_code == 403)
            except Exception as e:
                check('GET /api/admin/funnel (non-admin)', False, str(e))
    
    # Test 3: EMAIL STATUS & TEST ENDPOINTS
    if admin_token and admin_hdr:
        try:
            r = requests.get(f'{BASE}/admin/email/status', headers=admin_hdr, timeout=10)
            check('GET /api/admin/email/status (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                status = r.json()
                check('Email status has enabled field', 'enabled' in status)
                check('Email status has provider field', 'provider' in status)
                check('Email status enabled=true (Gmail configured)', status.get('enabled') is True, f"enabled={status.get('enabled')}")
                check('Email status provider=gmail_smtp', status.get('provider') == 'gmail_smtp', f"provider={status.get('provider')}")
                check('Email status has last_error field', 'last_error' in status)
                check('Email status has verified field', 'verified' in status)
                
                # Expected: last_error mentions App Password failure (535)
                last_error = status.get('last_error') or ''
                if last_error:
                    check('Email status last_error mentions auth failure', '535' in last_error or 'auth' in last_error.lower() or 'password' in last_error.lower(), 
                          f"last_error={last_error[:100]}")
                    print(f'   ✓ Gmail SMTP auth failure detected (expected): {last_error[:80]}')
                
                check('Email status verified=false (auth failed)', status.get('verified') is False, f"verified={status.get('verified')}")
        except Exception as e:
            check('GET /api/admin/email/status', False, str(e))
        
        # Test send test email (expected to fail with 535, but gracefully)
        try:
            r = requests.post(f'{BASE}/admin/email/test', headers=admin_hdr, timeout=10)
            check('POST /api/admin/email/test (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                result = r.json()
                check('Test email response has status field', 'status' in result)
                check('Test email response has to field', 'to' in result)
                
                # Expected: status is 'failed — logged only' (Gmail 535 is EXPECTED)
                status_text = result.get('status', '')
                check('Test email status is failed/logged (expected)', 'failed' in status_text.lower() or 'logged' in status_text.lower(), 
                      f"status={status_text}")
                print(f'   ✓ Test email gracefully failed (expected): {status_text}')
        except Exception as e:
            check('POST /api/admin/email/test', False, str(e))
        
        # Test non-admin gets 403
        if token and hdr:
            try:
                r = requests.get(f'{BASE}/admin/email/status', headers=hdr, timeout=10)
                check('GET /api/admin/email/status (non-admin) returns 403', r.status_code == 403)
            except Exception as e:
                check('GET /api/admin/email/status (non-admin)', False, str(e))
    
    # Test 4: COMMUNITY MEMBER PROFILES
    if admin_token and admin_hdr:
        # Get admin's own profile
        admin_user_id = None
        try:
            r = requests.get(f'{BASE}/auth/me', headers=admin_hdr, timeout=10)
            if r.status_code == 200:
                admin_user_id = r.json()['user']['id']
        except Exception:
            pass
        
        if admin_user_id:
            try:
                r = requests.get(f'{BASE}/community/members/{admin_user_id}', headers=admin_hdr, timeout=10)
                check('GET /api/community/members/{uid} (admin profile) returns 200', r.status_code == 200, r.text)
                if r.status_code == 200:
                    profile = r.json()
                    check('Member profile has id', profile.get('id') == admin_user_id)
                    check('Member profile has name', 'name' in profile)
                    check('Member profile has role', 'role' in profile)
                    check('Member profile role=admin', profile.get('role') == 'admin', f"role={profile.get('role')}")
                    check('Member profile has is_premium', 'is_premium' in profile)
                    check('Member profile is_premium=true (admin)', profile.get('is_premium') is True, f"is_premium={profile.get('is_premium')}")
                    check('Member profile has joined', 'joined' in profile)
                    check('Member profile has thread_count', 'thread_count' in profile)
                    check('Member profile has reply_count', 'reply_count' in profile)
                    check('Member profile has recent_threads array', 'recent_threads' in profile and isinstance(profile['recent_threads'], list))
                    
                    # Admin should have threads from previous tests
                    if profile.get('thread_count', 0) > 0:
                        print(f'   ✓ Admin profile: {profile["thread_count"]} threads, {profile["reply_count"]} replies')
            except Exception as e:
                check('GET /api/community/members/{uid} (admin)', False, str(e))
        
        # Test free (non-premium) user gets 403
        if token and hdr:
            try:
                r = requests.get(f'{BASE}/community/members/{admin_user_id}', headers=hdr, timeout=10)
                check('GET /api/community/members/{uid} (free user) returns 403', r.status_code == 403)
            except Exception as e:
                check('GET /api/community/members/{uid} (free user)', False, str(e))
        
        # Test unknown uid returns 404
        try:
            r = requests.get(f'{BASE}/community/members/unknown-user-id-12345', headers=admin_hdr, timeout=10)
            check('GET /api/community/members/{uid} (unknown uid) returns 404', r.status_code == 404)
        except Exception as e:
            check('GET /api/community/members/{uid} (unknown)', False, str(e))
    
    # Test 5: SCHEDULED ANNOUNCEMENTS
    scheduled_ann_id = None
    if admin_token and admin_hdr:
        # Create announcement with future publish_at
        from datetime import datetime, timedelta
        future_time = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        
        try:
            r = requests.post(f'{BASE}/community/announcements', json={
                'title': 'AMA next week',
                'body': 'Join us for an AMA session next week!',
                'publish_at': future_time
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/announcements with future publish_at returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                ann = r.json()
                scheduled_ann_id = ann.get('id')
                check('Scheduled announcement has scheduled=true', ann.get('scheduled') is True, f"scheduled={ann.get('scheduled')}")
                check('Scheduled announcement has publish_at', 'publish_at' in ann)
                print(f'   ✓ Created scheduled announcement: {scheduled_ann_id}')
        except Exception as e:
            check('POST /api/community/announcements (scheduled)', False, str(e))
        
        # Test invalid publish_at string returns 400
        try:
            r = requests.post(f'{BASE}/community/announcements', json={
                'title': 'Invalid Schedule',
                'body': 'This should fail.',
                'publish_at': 'not-a-valid-datetime'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/announcements with invalid publish_at returns 400', r.status_code == 400)
        except Exception as e:
            check('POST /api/community/announcements (invalid publish_at)', False, str(e))
        
        # Test announcement without publish_at publishes immediately
        immediate_ann_id = None
        try:
            r = requests.post(f'{BASE}/community/announcements', json={
                'title': 'Immediate Announcement',
                'body': 'This publishes right away.'
            }, headers=admin_hdr, timeout=10)
            check('POST /api/community/announcements without publish_at returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                ann = r.json()
                immediate_ann_id = ann.get('id')
                check('Immediate announcement has scheduled=false', ann.get('scheduled') is False, f"scheduled={ann.get('scheduled')}")
        except Exception as e:
            check('POST /api/community/announcements (immediate)', False, str(e))
        
        # Test GET announcements as admin includes scheduled
        try:
            r = requests.get(f'{BASE}/community/announcements', headers=admin_hdr, timeout=10)
            check('GET /api/community/announcements (admin) returns 200', r.status_code == 200, r.text)
            if r.status_code == 200:
                anns = r.json().get('announcements', [])
                scheduled_anns = [a for a in anns if a.get('scheduled')]
                check('Admin sees scheduled announcements', len(scheduled_anns) > 0, f'found {len(scheduled_anns)} scheduled')
                
                # Verify the scheduled announcement we created is in the list
                if scheduled_ann_id:
                    found = any(a['id'] == scheduled_ann_id for a in anns)
                    check('Admin sees the scheduled announcement we created', found)
        except Exception as e:
            check('GET /api/community/announcements (admin)', False, str(e))
        
        # Clean up: delete immediate announcement
        if immediate_ann_id:
            try:
                requests.delete(f'{BASE}/community/announcements/{immediate_ann_id}', headers=admin_hdr, timeout=10)
            except Exception:
                pass
        
        # KEEP the scheduled announcement "AMA next week" for frontend testing
        print('   ✓ Scheduled announcement "AMA next week" kept for frontend testing')

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
