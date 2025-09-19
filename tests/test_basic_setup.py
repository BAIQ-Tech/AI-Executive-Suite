"""
Basic test to verify test setup is working
"""

def test_basic_math():
    """Test basic math operations"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5


def test_string_operations():
    """Test string operations"""
    text = "Hello World"
    assert text.lower() == "hello world"
    assert text.upper() == "HELLO WORLD"
    assert len(text) == 11


def test_list_operations():
    """Test list operations"""
    items = [1, 2, 3, 4, 5]
    assert len(items) == 5
    assert sum(items) == 15
    assert max(items) == 5
    assert min(items) == 1


def test_dict_operations():
    """Test dictionary operations"""
    data = {'name': 'test', 'value': 42}
    assert data['name'] == 'test'
    assert data['value'] == 42
    assert len(data) == 2
    assert 'name' in data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])