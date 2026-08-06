"""POC test: server-side paywall + subscription entitlement transitions.
Runs against local backend (supervisor, port 8001).
"""
import requests
import uuid
import sys

BASE = 'http://localhost:8001/api'
PASS, FAIL = 0, 0


def check(name, cond, detail=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  PASS: {name}')
    else:
        FAIL += 1
        print(f'  FAIL: {name} {detail}')


def main():
    print('=== POC: The Trading Narrative core (paywall + subscription) ===')

    # 0. health + seed
    r = requests.get(f'{BASE}/health')
    check('health endpoint', r.status_code == 200, r.text)
    r = requests.get(f'{BASE}/posts')
    posts = r.json().get('posts', [])
    check('seeded 12 posts', len(posts) == 12, f'got {len(posts)}')
    premium_posts = [p for p in posts if p['tier'] == 'premium']
    free_posts = [p for p in posts if p['tier'] == 'free']
    check('has premium + free posts', len(premium_posts) > 0 and len(free_posts) > 0)
    check('list endpoint never returns content_blocks', all('content_blocks' not in p for p in posts))
    prem_slug = premium_posts[0]['slug']
    free_slug = free_posts[0]['slug']

    # Story 1: unauth reader gets only preview on premium post
    r = requests.get(f'{BASE}/posts/{prem_slug}')
    d = r.json()
    check('premium post locked for anon', d['is_locked'] is True)
    check('anon gets only 3 preview blocks', d['shown_blocks'] == 3 and len(d['content_blocks']) == 3,
          f"shown={d['shown_blocks']}")
    check('total_blocks > shown (content withheld server-side)', d['total_blocks'] > d['shown_blocks'])
    check('related posts present', len(d.get('related', [])) > 0)

    # free post fully open for anon
    r = requests.get(f'{BASE}/posts/{free_slug}')
    d = r.json()
    check('free post unlocked for anon', d['is_locked'] is False and len(d['content_blocks']) == d['total_blocks'])

    # register a free user
    email = f'poc-{uuid.uuid4().hex[:8]}@test.com'
    r = requests.post(f'{BASE}/auth/register', json={'email': email, 'password': 'test1234', 'name': 'POC User'})
    check('register works', r.status_code == 200, r.text)
    token = r.json()['token']
    hdr = {'Authorization': f'Bearer {token}'}

    # login works
    r = requests.post(f'{BASE}/auth/login', json={'email': email, 'password': 'test1234'})
    check('login works', r.status_code == 200 and r.json()['user']['is_premium'] is False)

    # free (logged-in, non-premium) user still gets preview only
    r = requests.get(f'{BASE}/posts/{prem_slug}', headers=hdr)
    d = r.json()
    check('free user still locked on premium post', d['is_locked'] is True and d['shown_blocks'] == 3)

    # Story 2: mock checkout upgrades immediately
    r = requests.post(f'{BASE}/billing/checkout', json={'plan': 'monthly'}, headers=hdr)
    check('mock checkout succeeds', r.status_code == 200, r.text)
    inv = r.json().get('invoice', {})
    check('invoice created with amount', inv.get('amount') == 8.0 and inv.get('status') == 'paid')

    r = requests.get(f'{BASE}/auth/me', headers=hdr)
    check('user now premium', r.json()['user']['is_premium'] is True)

    # Story 3: premium user gets FULL content
    r = requests.get(f'{BASE}/posts/{prem_slug}', headers=hdr)
    d = r.json()
    check('premium user gets full content', d['is_locked'] is False and d['shown_blocks'] == d['total_blocks'],
          f"shown={d['shown_blocks']} total={d['total_blocks']}")

    # billing history
    r = requests.get(f'{BASE}/billing/invoices', headers=hdr)
    check('billing history has invoice', len(r.json()['invoices']) == 1)

    # duplicate checkout blocked
    r = requests.post(f'{BASE}/billing/checkout', json={'plan': 'annual'}, headers=hdr)
    check('duplicate checkout rejected', r.status_code == 400)

    # Story 4: cancel -> immediate revert to preview
    r = requests.post(f'{BASE}/billing/cancel', headers=hdr)
    check('cancel works', r.status_code == 200, r.text)
    r = requests.get(f'{BASE}/posts/{prem_slug}', headers=hdr)
    d = r.json()
    check('after cancel, locked again', d['is_locked'] is True and d['shown_blocks'] == 3)

    # Story 5: admin can flip tier and gating changes instantly
    r = requests.post(f'{BASE}/auth/login', json={'email': 'admin@tradingnarrative.com', 'password': 'Admin@2025'})
    check('admin login', r.status_code == 200, r.text)
    admin_hdr = {'Authorization': f"Bearer {r.json()['token']}"}
    r = requests.get(f'{BASE}/admin/posts', headers=admin_hdr)
    check('admin lists posts', r.status_code == 200)
    target = next(p for p in r.json()['posts'] if p['slug'] == free_slug)
    r = requests.get(f"{BASE}/admin/posts/{target['id']}", headers=admin_hdr)
    full = r.json()
    body = {k: full[k] for k in ('title', 'excerpt', 'category', 'cover_image', 'content_blocks', 'featured', 'status')}
    body['tier'] = 'premium'
    body['publish_at'] = full.get('publish_at')
    r = requests.put(f"{BASE}/admin/posts/{target['id']}", json=body, headers=admin_hdr)
    check('admin flips post to premium', r.status_code == 200, r.text)
    r = requests.get(f'{BASE}/posts/{free_slug}')
    check('flipped post now locked for anon', r.json()['is_locked'] is True)
    body['tier'] = 'free'
    r = requests.put(f"{BASE}/admin/posts/{target['id']}", json=body, headers=admin_hdr)
    r = requests.get(f'{BASE}/posts/{free_slug}')
    check('flipped back to free, unlocked', r.json()['is_locked'] is False)

    # admin route protection
    r = requests.get(f'{BASE}/admin/posts', headers=hdr)
    check('non-admin blocked from admin routes', r.status_code == 403)

    # magic link flow (mocked email)
    ml_email = f'magic-{uuid.uuid4().hex[:8]}@test.com'
    r = requests.post(f'{BASE}/auth/magic-link/request', json={'email': ml_email})
    check('magic link request (mocked)', r.status_code == 200 and 'magic_link' in r.json(), r.text)
    ml_token = r.json()['magic_link'].split('token=')[1]
    r = requests.post(f'{BASE}/auth/magic-link/verify', json={'token': ml_token})
    check('magic link verify creates session', r.status_code == 200 and 'token' in r.json(), r.text)
    r = requests.post(f'{BASE}/auth/magic-link/verify', json={'token': ml_token})
    check('magic link single-use', r.status_code == 400)

    # newsletter
    nl_email = f'nl-{uuid.uuid4().hex[:8]}@test.com'
    r = requests.post(f'{BASE}/newsletter/subscribe', json={'email': nl_email, 'source': 'poc'})
    check('newsletter subscribe', r.status_code == 200 and r.json()['ok'])
    r = requests.post(f'{BASE}/newsletter/subscribe', json={'email': nl_email, 'source': 'poc'})
    check('newsletter dedupe', r.json().get('already') is True)

    # sitemap
    r = requests.get(f'{BASE}/sitemap.xml')
    check('sitemap served', r.status_code == 200 and '<urlset' in r.text)

    print(f'\n=== RESULT: {PASS} passed, {FAIL} failed ===')
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == '__main__':
    main()
