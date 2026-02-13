"""
Tests for the Flask app endpoints
"""
import pytest
from mirrsearch.app import create_app


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


def test_home_endpoint(client):
    """Test the home endpoint returns the index.html template"""
    response = client.get('/')
    assert response.status_code == 200


def test_search_endpoint_exists(client):
    """Test that the search endpoint exists and returns 200"""
    response = client.get('/search/')
    assert response.status_code == 200


def test_search_returns_list(client):
    """Test that search endpoint returns a list"""
    response = client.get('/search/')
    assert response.status_code == 200
    # Flask will auto-convert the list to JSON
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)


def test_search_returns_dummy_data(client):
    """Test that search endpoint returns the expected dummy data"""
    response = client.get('/search/')
    data = response.get_json()
    
    # Should return a list with 3 items
    assert len(data) == 3
    assert data[0] == "Test"
    assert data[1] == "Dummy"
    # Third item is the search parameter (None if not provided)
    assert data[2] is None


def test_search_with_query_parameter(client):
    """Test that search endpoint accepts and returns query parameter"""
    response = client.get('/search/?str=my_search_query')
    data = response.get_json()
    
    assert len(data) == 3
    assert data[0] == "Test"
    assert data[1] == "Dummy"
    assert data[2] == "my_search_query"


def test_search_with_different_query_parameters(client):
    """Test search endpoint with various query strings"""
    # Test with simple string
    response1 = client.get('/search/?str=hello')
    data1 = response1.get_json()
    assert data1[2] == "hello"
    
    # Test with multiple words
    response2 = client.get('/search/?str=hello world')
    data2 = response2.get_json()
    assert data2[2] == "hello world"
    
    # Test with empty string
    response3 = client.get('/search/?str=')
    data3 = response3.get_json()
    assert data3[2] == ""