"""Tests for iteration 2 features: Accounts CRUD, Bill reminders, Spending trends."""
from datetime import datetime, timezone
import pytest


# ---------- Accounts CRUD ----------
class TestAccountsCRUD:
    def test_seeded_accounts_have_3(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/accounts', headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        accs = r.json()
        assert len(accs) == 3
        for a in accs:
            assert 'id' in a and 'name' in a and 'type' in a and 'balance' in a
            assert '_id' not in a

    def test_create_rename_delete_account(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        # CREATE
        payload = {'name': 'TEST_Kotak', 'type': 'bank', 'balance': 10000, 'color': '#0EA5E9'}
        r = api.post(f'{base_url}/api/accounts', headers=h, json=payload, timeout=15)
        assert r.status_code == 200
        acc = r.json()
        assert acc['name'] == 'TEST_Kotak'
        assert acc['balance'] == 10000
        assert acc['type'] == 'bank'
        aid = acc['id']

        # GET verify persisted
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        assert any(a['id'] == aid and a['name'] == 'TEST_Kotak' for a in accs)

        # RENAME
        r = api.put(f'{base_url}/api/accounts/{aid}', headers=h,
                    json={'name': 'TEST_Kotak_Renamed'}, timeout=15)
        assert r.status_code == 200
        assert r.json()['name'] == 'TEST_Kotak_Renamed'
        # verify via GET
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        assert any(a['id'] == aid and a['name'] == 'TEST_Kotak_Renamed' for a in accs)

        # EDIT balance & type
        r = api.put(f'{base_url}/api/accounts/{aid}', headers=h,
                    json={'balance': 12345.5, 'type': 'wallet'}, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body['balance'] == 12345.5
        assert body['type'] == 'wallet'

        # DELETE
        r = api.delete(f'{base_url}/api/accounts/{aid}', headers=h, timeout=15)
        assert r.status_code == 200
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        assert not any(a['id'] == aid for a in accs)


# ---------- Bills ----------
class TestBills:
    def test_seed_creates_4_bills_with_computed_fields(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/bills', headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        bills = r.json()
        assert len(bills) == 4
        for b in bills:
            assert 'next_due' in b
            assert 'days_until' in b
            assert 'paid_this_month' in b
            assert b['paid_this_month'] is False
            assert isinstance(b['days_until'], int)
            assert '_id' not in b
        # sorted ascending by days_until
        du = [b['days_until'] for b in bills]
        assert du == sorted(du)

    def test_create_edit_delete_bill(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        r = api.post(f'{base_url}/api/bills', headers=h,
                     json={'name': 'TEST_Gym', 'amount': 999, 'category': 'health',
                           'due_day': 15}, timeout=15)
        assert r.status_code == 200
        bill = r.json()
        assert bill['name'] == 'TEST_Gym'
        assert bill['due_day'] == 15
        assert 'next_due' in bill and 'days_until' in bill
        bid = bill['id']

        # EDIT
        r = api.put(f'{base_url}/api/bills/{bid}', headers=h,
                    json={'name': 'TEST_Gym_Pro', 'amount': 1299, 'category': 'health',
                          'due_day': 20}, timeout=15)
        assert r.status_code == 200

        bills = api.get(f'{base_url}/api/bills', headers=h, timeout=15).json()
        updated = next(b for b in bills if b['id'] == bid)
        assert updated['name'] == 'TEST_Gym_Pro'
        assert updated['amount'] == 1299
        assert updated['due_day'] == 20

        # DELETE
        r = api.delete(f'{base_url}/api/bills/{bid}', headers=h, timeout=15)
        assert r.status_code == 200
        bills = api.get(f'{base_url}/api/bills', headers=h, timeout=15).json()
        assert not any(b['id'] == bid for b in bills)

    def test_pay_bill_creates_txn_decrements_balance_and_marks_paid(self, api, base_url, fresh_user):
        h = fresh_user['headers']
        # find first seeded bill with an account
        bills = api.get(f'{base_url}/api/bills', headers=h, timeout=15).json()
        assert bills, 'No bills seeded'
        # Pick one that isn't yet paid and has account_id
        bill = next((b for b in bills if b.get('account_id') and not b['paid_this_month']), None)
        assert bill is not None
        bid, aid, amt = bill['id'], bill['account_id'], bill['amount']

        # starting balance
        accs = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        starting = next(a['balance'] for a in accs if a['id'] == aid)

        # starting txn count
        txns_before = api.get(f'{base_url}/api/transactions', headers=h, timeout=15).json()
        n_before = len(txns_before)

        # PAY
        r = api.post(f'{base_url}/api/bills/{bid}/pay', headers=h, timeout=15)
        assert r.status_code == 200

        # verify paid_this_month flip
        bills2 = api.get(f'{base_url}/api/bills', headers=h, timeout=15).json()
        paid = next(b for b in bills2 if b['id'] == bid)
        assert paid['paid_this_month'] is True

        # balance decreased by amt
        accs2 = api.get(f'{base_url}/api/accounts', headers=h, timeout=15).json()
        new_bal = next(a['balance'] for a in accs2 if a['id'] == aid)
        assert abs(new_bal - (starting - amt)) < 0.01

        # transaction added
        txns_after = api.get(f'{base_url}/api/transactions', headers=h, timeout=15).json()
        assert len(txns_after) == n_before + 1
        latest = next(t for t in txns_after if t['title'] == bill['name']
                      and t['amount'] == amt and t['type'] == 'expense')
        assert latest['note'] == 'Bill payment'

    def test_pay_nonexistent_bill_404(self, api, base_url, fresh_user):
        r = api.post(f'{base_url}/api/bills/does-not-exist/pay',
                     headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 404


# ---------- Trends ----------
class TestTrends:
    def test_trends_returns_6_months(self, api, base_url, fresh_user):
        r = api.get(f'{base_url}/api/dashboard/trends',
                    headers=fresh_user['headers'], timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert 'months' in data
        months = data['months']
        assert len(months) == 6
        for m in months:
            assert 'year' in m and 'month' in m
            assert 'income' in m and 'expense' in m
            assert isinstance(m['income'], (int, float))
            assert isinstance(m['expense'], (int, float))
            assert 1 <= m['month'] <= 12

        # last entry is current month
        now = datetime.now(timezone.utc)
        assert months[-1]['year'] == now.year
        assert months[-1]['month'] == now.month
        # current month should have income & expense from the 12 seeded txns
        current = months[-1]
        assert current['income'] > 0
        assert current['expense'] > 0

    def test_trends_requires_auth(self, api, base_url):
        r = api.get(f'{base_url}/api/dashboard/trends', timeout=15)
        assert r.status_code == 401
