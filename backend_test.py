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
