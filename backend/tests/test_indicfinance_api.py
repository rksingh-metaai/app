"""IndicFinance backend regression tests.
Covers: auth (register/login/me/language), dashboard, transactions, budgets,
goals, and AI assistant.
"""
import time
import uuid
import pytest


# ---------- Auth ----------
class TestAuth:
    def test_register_seeds_data_and_returns_token(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        # 3 accounts seeded
        r = api.get(f'{base_url}/api/accounts', headers=h, timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 3
        # 12 transactions seeded
        r = api.get(f'{base_url}/api/transactions', headers=h, timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 12
        # 4 budgets seeded
        r = api.get(f'{base_url}/api/budgets', headers=h, timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 4
        # 3 goals seeded
        r = api.get(f'{base_url}/api/goals', headers=h, timeout=15)
        assert r.status_code == 200
        assert len(r.json()) == 3
        # user shape
        u = fresh_user['user']
        assert u['language'] == 'hi'
        assert u['currency'] == 'INR'
        assert '@' in u['email']

    def test_register_duplicate_email_409(self, api, base_url, fresh_user):
        r = api.post(f'{base_url}/api/auth/register', json={
            'name': 'dup', 'email': fresh_user['user']['email'],
            'password': 'test123', 'language': 'en',
        }, timeout=15)
        assert r.status_code == 409

    def test_login_success(self, api, base_url, fresh_user):
        r = api.post(f'{base_url}/api/auth/login', json={
            'email': fresh_user['user']['email'], 'password': 'test123',
        }, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert 'token' in data and 'user' in data
        assert data['user']['email'] == fresh_user['user']['email']

    def test_login_wrong_password_401(self, api, base_url, fresh_user):
        r = api.post(f'{base_url}/api/auth/login', json={
            'email': fresh_user['user']['email'], 'password': 'wrongpass',
        }, timeout=15)
        assert r.status_code == 401

    def test_me_returns_user(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/auth/me', headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        assert r.json()['id'] == fresh_user['user']['id']

    def test_me_without_token_401(self, api, base_url):
        r = api.get(f'{base_url}/api/auth/me', timeout=15)
        assert r.status_code == 401

    def test_update_language(self, api, base_url, fresh_user):
        r = api.put(f'{base_url}/api/auth/language',
                    headers=fresh_user['headers'],
                    json={'language': 'ta'}, timeout=15)
        assert r.status_code == 200
        assert r.json()['language'] == 'ta'
        # revert to hi for downstream tests (AI test asserts hi reply)
        api.put(f'{base_url}/api/auth/language',
                headers=fresh_user['headers'],
                json={'language': 'hi'}, timeout=15)


# ---------- Dashboard ----------
class TestDashboard:
    def test_dashboard_summary_shape(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/dashboard/summary',
                    headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ('total_balance', 'income', 'expense', 'savings',
                  'spending_by_category', 'recent_transactions'):
            assert k in d, f'missing {k}'
        assert isinstance(d['spending_by_category'], list)
        assert isinstance(d['recent_transactions'], list)
        assert len(d['recent_transactions']) <= 5
        # savings math
        assert abs(d['savings'] - (d['income'] - d['expense'])) < 0.01


# ---------- Transactions ----------
class TestTransactions:
    def test_create_expense_updates_balance_and_delete_reverts(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        accounts = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        acc = accounts[0]
        starting_balance = acc['balance']

        payload = {
            'account_id': acc['id'],
            'title': 'TEST_Coffee',
            'amount': 250,
            'type': 'expense',
            'category': 'food',
        }
        r = api.post(f'{base_url}/api/transactions', headers=h, json=payload, timeout=15)
        assert r.status_code == 200
        txn = r.json()
        assert txn['amount'] == 250 and txn['type'] == 'expense'

        # verify GET returns it
        txns = api.get(f'{base_url}/api/transactions', headers=h, timeout=15).json()
        assert any(t['id'] == txn['id'] for t in txns)

        # balance decreased by 250
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        new_bal = next(a['balance'] for a in accs if a['id'] == acc['id'])
        assert abs(new_bal - (starting_balance - 250)) < 0.01

        # delete reverts balance
        r = api.delete(f'{base_url}/api/transactions/{txn["id"]}', headers=h, timeout=15)
        assert r.status_code == 200
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        reverted = next(a['balance'] for a in accs if a['id'] == acc['id'])
        assert abs(reverted - starting_balance) < 0.01

        # soft-delete: not in list anymore
        txns = api.get(f'{base_url}/api/transactions', headers=h, timeout=15).json()
        assert not any(t['id'] == txn['id'] for t in txns)

    def test_filter_by_type(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        r = api.get(f'{base_url}/api/transactions?type=income', headers=h, timeout=15)
        assert r.status_code == 200
        assert all(t['type'] == 'income' for t in r.json())


# ---------- Budgets ----------
class TestBudgets:
    def test_budget_includes_spent(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/budgets', headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        for b in r.json():
            assert 'spent' in b
            assert isinstance(b['spent'], (int, float))

    def test_create_and_delete_budget(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        r = api.post(f'{base_url}/api/budgets', headers=h,
                     json={'name': 'TEST_Entertainment', 'category': 'entertainment',
                           'limit': 3000, 'period': 'monthly'}, timeout=15)
        assert r.status_code == 200
        bid = r.json()['id']
        # verify present
        ids = [b['id'] for b in api.get(f'{base_url}/api/budgets', headers=h, timeout=15).json()]
        assert bid in ids
        # delete
        r = api.delete(f'{base_url}/api/budgets/{bid}', headers=h, timeout=15)
        assert r.status_code == 200
        ids = [b['id'] for b in api.get(f'{base_url}/api/budgets', headers=h, timeout=15).json()]
        assert bid not in ids


# ---------- Goals ----------
class TestGoals:
    def test_create_add_and_delete_goal(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        r = api.post(f'{base_url}/api/goals', headers=h,
                     json={'name': 'TEST_Bike', 'target': 20000, 'saved': 1000}, timeout=15)
        assert r.status_code == 200
        gid = r.json()['id']
        assert r.json()['saved'] == 1000

        # add money
        r = api.post(f'{base_url}/api/goals/{gid}/add', headers=h,
                     json={'amount': 500}, timeout=15)
        assert r.status_code == 200
        assert r.json()['saved'] == 1500

        # delete
        r = api.delete(f'{base_url}/api/goals/{gid}', headers=h, timeout=15)
        assert r.status_code == 200
        ids = [g['id'] for g in api.get(f'{base_url}/api/goals', headers=h, timeout=15).json()]
        assert gid not in ids


# ---------- AI Assistant ----------
class TestAssistant:
    def test_chat_replies_and_history_persists(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        r = api.post(f'{base_url}/api/assistant/chat', headers=h,
                     json={'message': 'How much did I spend this month?'}, timeout=90)
        assert r.status_code == 200, r.text
        reply = r.json().get('reply', '')
        assert isinstance(reply, str) and len(reply) > 0
        assert 'couldn' not in reply.lower() or 'sorry' not in reply.lower(), (
            f'AI returned fallback error: {reply}')

        # history contains both user and assistant messages
        time.sleep(0.5)
        r = api.get(f'{base_url}/api/assistant/history', headers=h, timeout=15)
        assert r.status_code == 200
        roles = [m['role'] for m in r.json()]
        assert 'user' in roles and 'assistant' in roles
