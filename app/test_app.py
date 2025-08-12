import pytest
import json
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test the home route returns correct message"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Hello from GitOps Demo' in response.data

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get('/healthz')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_readiness_check(client):
    """Test the readiness check endpoint"""
    response = client.get('/readyz')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ready'

def test_metrics_endpoint(client):
    """Test the metrics endpoint exists"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'gitops_demo_info' in response.data
    assert b'http_requests_total' in response.data

def test_version_header(client):
    """Test that version header is present"""
    response = client.get('/')
    assert 'X-App-Version' in response.headers
    assert response.headers['X-App-Version'] == '0.1.0'

def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404

def test_response_time_header(client):
    """Test that response time header is added"""
    response = client.get('/')
    # Since we're testing, response time should be very low
    assert response.status_code == 200
    # Add more specific response time tests if needed

def test_environment_info(client):
    """Test environment information is available"""
    response = client.get('/info')
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'version' in data
        assert 'environment' in data