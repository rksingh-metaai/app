import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://indic-banking-app.preview.emergentagent.com').rstrip('/')


@pytest.fixture(scope='session')
def base_url():
    return BASE_URL


@pytest.fixture(scope='session')
def api():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s


@pytest.fixture(scope='session')
def fresh_user(api):
    """Register a fresh test user and return {token, user, headers}."""
    email = f"TEST_{uuid.uuid4().hex[:10]}@example.com"
    payload = {
        'name': 'TEST Aarav',
        'email': email,
        'password': 'test123',
        'language': 'hi',
    }
    r = api.post(f'{BASE_URL}/api/auth/register', json=payload, timeout=30)
    assert r.status_code == 200, f'Register failed: {r.status_code} {r.text}'
    data = r.json()
    return {
        'token': data['token'],
        'user': data['user'],
        'password': 'test123',
        'headers': {'Authorization': f"Bearer {data['token']}", 'Content-Type': 'application/json'},
    }
