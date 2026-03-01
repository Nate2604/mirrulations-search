"""
Tests for the Flask app endpoints
"""
# pylint: disable=redefined-outer-name
import pytest
from mock_db import MockDBLayer
from mirrsearch.app import create_app


@pytest.fixture
def app(tmp_path):
    """Create and configure a test app instance"""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html></html>")
    test_app = create_app(dist_dir=str(dist), db_layer=MockDBLayer())
    test_app.config['TESTING'] = True
    return test_app


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
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)


def test_search_returns_dummy_data(client):
    """Test that search endpoint returns expected data"""
    response = client.get('/search/?str=ESRD')
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'docket_id' in data[0]
    assert 'title' in data[0]
    assert 'ESRD' in data[0]['title'] or 'End-Stage Renal Disease' in data[0]['title']


def test_search_with_query_parameter(client):
    """Test that search endpoint accepts and returns query parameter"""
    response = client.get('/search/?str=ESRD')
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any('ESRD' in item['title'] for item in data)


def test_search_with_different_query_parameters(client):
    """Test search endpoint with various query strings"""
    data1 = client.get('/search/?str=CMS-2025-024').get_json()
    assert isinstance(data1, list)
    assert len(data1) > 0
    assert all(item['docket_id'].startswith('CMS-2025-024') for item in data1)

    data2 = client.get('/search/?str=ESRD').get_json()
    assert isinstance(data2, list)
    assert len(data2) > 0
    assert any('ESRD' in item['title'] for item in data2)

    data3 = client.get('/search/?str=CMS').get_json()
    assert isinstance(data3, list)
    assert len(data3) > 0
    assert all(item['agency_id'] == 'CMS' for item in data3)


def test_search_without_filter_returns_all_matches(client):
    """Omitting the filter param returns all matching results"""
    response = client.get('/search/?str=renal')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert len({item['document_type'] for item in data}) >= 1


def test_search_with_valid_filter_returns_matching_document_type(client):
    """document_type param restricts results to the specified document_type"""
    response = client.get('/search/?str=renal&document_type=Proposed Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(item['document_type'] == 'Proposed Rule' for item in data)


def test_search_with_filter_only_affects_document_type(client):
    """Filtered results still match the search query"""
    response = client.get('/search/?str=ESRD&document_type=Proposed Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert 'ESRD' in item['title'] or 'esrd' in item['title'].lower()
        assert item['document_type'] == 'Proposed Rule'


def test_search_with_nonexistent_filter_returns_empty_list(client):
    """A filter value matching no document_type returns an empty list"""
    response = client.get('/search/?str=renal&document_type=Final Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_filter_is_case_insensitive(client):
    """The filter comparison is case-insensitive"""
    data_lower = client.get('/search/?str=renal&document_type=proposed rule').get_json()
    data_upper = client.get('/search/?str=renal&document_type=PROPOSED RULE').get_json()
    data_mixed = client.get('/search/?str=renal&document_type=Proposed Rule').get_json()
    assert len(data_lower) == len(data_upper) == len(data_mixed)
    assert data_lower == data_upper == data_mixed


def test_search_filter_without_query_string_uses_default(client):
    """Filter works even when no str param is provided (falls back to example_query)"""
    response = client.get('/search/?document_type=Proposed Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0  # "example_query" matches nothing in mock data


def test_search_filter_result_structure(client):
    """Filtered results contain all required fields"""
    response = client.get('/search/?str=CMS&document_type=Proposed Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    required_fields = ['docket_id', 'title', 'cfrPart', 'agency_id', 'document_type']
    for item in data:
        for field in required_fields:
            assert field in item, f"Filtered result missing field: {field}"


def test_search_with_agency_filter(client):
    """Agency param restricts results to the specified agency_id"""
    response = client.get('/search/?str=renal&agency=CMS')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(item['agency_id'] == 'CMS' for item in data)


def test_search_with_nonexistent_agency_returns_empty_list(client):
    """An agency value matching no agency_id returns an empty list"""
    response = client.get('/search/?str=renal&agency=FDA')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_agency_filter_is_case_insensitive(client):
    """Agency filter comparison is case-insensitive"""
    data_lower = client.get('/search/?str=renal&agency=cms').get_json()
    data_upper = client.get('/search/?str=renal&agency=CMS').get_json()
    assert len(data_lower) == len(data_upper)
    assert data_lower == data_upper


def test_search_with_agency_and_document_type(client):
    """Both agency and document_type params can be combined"""
    response = client.get('/search/?str=renal&agency=CMS&document_type=Proposed Rule')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert item['agency_id'] == 'CMS'
        assert item['document_type'] == 'Proposed Rule'
