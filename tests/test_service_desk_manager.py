import json
from unittest.mock import Mock, patch

import pytest
import requests

from atlassianforms.form.parser import ServiceDeskForm
from atlassianforms.manager import (
    ServiceDeskFormFilled,
    ServiceDeskManager,
    ServiceDeskRequestError,
    remove_disposable_keys,
)


@pytest.fixture
def service_desk_manager():
    return ServiceDeskManager("https://example.atlassian.net", "username", "token")


@pytest.fixture
def mock_response():
    mock = Mock()
    mock.raise_for_status = Mock()
    return mock


@patch("requests.post")
def test_create_request_success(mock_post, service_desk_manager):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"issueKey": "SD-123"}
    mock_post.return_value = mock_response

    form = ServiceDeskForm(
        id="FORM-1",
        service_desk_id="1",
        request_type_id="10",
        project_id="PROJ-1",
        portal_name="Test Portal",
        form_name="Test Form",
        portal_description="Test Description",
        form_description_html="<p>Test Form Description</p>",
    )
    form_filled = ServiceDeskFormFilled(
        form=form, filled_values={"summary": "Test Issue"}
    )

    result = service_desk_manager.create_request(form_filled)

    assert result["issueKey"] == "SD-123"


@patch("requests.post")
def test_create_request_failure(mock_post, service_desk_manager):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response

    form = ServiceDeskForm(
        id="FORM-1",
        service_desk_id="1",
        request_type_id="10",
        project_id="PROJ-1",
        portal_name="Test Portal",
        form_name="Test Form",
        portal_description="Test Description",
        form_description_html="<p>Test Form Description</p>",
    )
    form_filled = ServiceDeskFormFilled(
        form=form, filled_values={"summary": "Test Issue"}
    )

    with pytest.raises(ServiceDeskRequestError) as excinfo:
        service_desk_manager.create_request(form_filled)

    assert "400" in str(excinfo.value)
    assert "Bad Request" in str(excinfo.value)


def test_remove_disposable_keys():
    test_data = {
        "keep": "value",
        "remove": "value",
        "nested": {"keep": "value", "remove": "value"},
        "list": [
            {"keep": "value", "remove": "value"},
            {"keep": "value", "remove": "value"},
        ],
    }
    disposable_keys = ["remove"]

    result = remove_disposable_keys(test_data, disposable_keys)

    assert "keep" in result
    assert "remove" not in result
    assert "keep" in result["nested"]
    assert "remove" not in result["nested"]
    assert "keep" in result["list"][0]
    assert "remove" not in result["list"][0]


@patch("requests.post")
def test_fetch_autocomplete_options(mock_post, service_desk_manager):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {"objectId": "OBJ-1", "label": "Option 1"},
            {"objectId": "OBJ-2", "label": "Option 2"},
        ]
    }
    mock_post.return_value = mock_response

    form_data = {
        "portalId": 1,
        "reqCreate": {
            "id": 10,
            "fields": [
                {
                    "fieldId": "customfield_10000",
                    "fieldType": "cmdbobjectpicker",
                    "autoCompleteUrl": "/autocomplete",
                    "label": "CMDB Object",
                    "description": "Select a CMDB object",
                    "required": True,
                    "displayed": True,
                }
            ],
        },
    }

    result = service_desk_manager._fetch_autocomplete_options(form_data)

    assert len(result) == 1
    assert result[0]["fieldId"] == "customfield_10000"
    assert result[0]["fieldType"] == "cmdbobjectpicker"
    assert result[0]["fieldLabel"] == "CMDB Object"
    assert len(result[0]["results"]) == 2
    assert result[0]["results"][0]["objectId"] == "OBJ-1"


if __name__ == "__main__":
    pytest.main()
