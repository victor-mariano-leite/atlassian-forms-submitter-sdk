from unittest.mock import Mock, patch

import pytest

from atlassianforms.client import FORM_DIDNT_FETCH_ERROR, ServiceDeskFormClient
from atlassianforms.form.manager import ServiceDeskFormManager
from atlassianforms.form.parser import ServiceDeskFormParser
from atlassianforms.manager import ServiceDeskManager
from atlassianforms.models.response import CreateRequestResponseParser


@pytest.fixture
def client():
    return ServiceDeskFormClient("https://example.atlassian.net", "username", "token")


@pytest.fixture
def mock_requests():
    with patch("atlassianforms.manager.requests") as mock:
        yield mock


@pytest.fixture
def mock_form_parser():
    with patch("atlassianforms.client.ServiceDeskFormParser") as mock:
        yield mock


@pytest.fixture
def mock_form_manager():
    with patch("atlassianforms.client.ServiceDeskFormManager") as mock:
        yield mock


@pytest.fixture
def mock_response_parser():
    with patch("atlassianforms.client.CreateRequestResponseParser") as mock:
        yield mock


def test_init(client):
    assert isinstance(client.service_desk_manager, ServiceDeskManager)
    assert client.form_manager is None


def test_list_fields_without_fetch(client):
    with pytest.raises(ValueError, match=FORM_DIDNT_FETCH_ERROR):
        client.list_fields()


def test_list_fields_with_fetch(client):
    client.form_manager = Mock()
    client.list_fields()
    client.form_manager.list_fields.assert_called_once()


def test_list_field_values_without_fetch(client):
    with pytest.raises(ValueError, match=FORM_DIDNT_FETCH_ERROR):
        client.list_field_values("field_name")


def test_list_field_values_with_fetch(client):
    client.form_manager = Mock()
    client.list_field_values("field_name")
    client.form_manager.list_field_values.assert_called_once_with("field_name")


def test_set_form_values_without_fetch(client):
    with pytest.raises(ValueError, match=FORM_DIDNT_FETCH_ERROR):
        client.set_form_values({"field": "value"})


def test_set_form_values_with_fetch(client):
    client.form_manager = Mock()
    client.form_manager.set_field_values.return_value = {"filled": "form"}
    result = client.set_form_values({"field": "value"})
    client.form_manager.set_field_values.assert_called_once_with({"field": "value"})
    assert result == {"filled": "form"}


@pytest.mark.parametrize(
    "method,args",
    [
        ("list_fields", []),
        ("list_field_values", ["field_name"]),
        ("set_form_values", [{"field": "value"}]),
    ],
)
def test_methods_raise_error_without_fetch(client, method, args):
    with pytest.raises(ValueError, match=FORM_DIDNT_FETCH_ERROR):
        getattr(client, method)(*args)


if __name__ == "__main__":
    pytest.main()
