import json
import urllib
from typing import Any, Dict

import pytest

from atlassianforms.form.manager import (
    ServiceDeskForm,
    ServiceDeskFormField,
    ServiceDeskFormFieldValue,
    ServiceDeskFormFilled,
    ServiceDeskFormManager,
)
from atlassianforms.validators.field import ServiceDeskFormValidator


@pytest.fixture
def sample_form():
    return ServiceDeskForm(
        id="FORM-1",
        service_desk_id="SD-1",
        request_type_id="RT-1",
        project_id="PROJ-1",
        portal_name="Test Portal",
        portal_description="Test Description",
        form_name="Test Form",
        form_description_html="<p>Test Form Description</p>",
        template_id=123,
        template_form_uuid="UUID-456",
        fields=[
            ServiceDeskFormField(
                field_type="text",
                field_id="summary",
                label="Summary",
                required=True,
                displayed=True,
                field_config_id="",
                description="",
                description_html="",
            ),
            ServiceDeskFormField(
                field_type="select",
                field_id="priority",
                label="Priority",
                required=True,
                displayed=True,
                field_config_id="",
                description="",
                description_html="",
                values=[
                    ServiceDeskFormFieldValue(value="high", label="High"),
                    ServiceDeskFormFieldValue(value="medium", label="Medium"),
                    ServiceDeskFormFieldValue(value="low", label="Low"),
                ],
            ),
            ServiceDeskFormField(
                field_type="rt",
                field_id="description",
                label="Description",
                required=True,
                displayed=True,
                field_config_id="",
                description="",
                description_html="",
                is_proforma_field=True,
                proforma_question_id="PROFORMA-1",
            ),
        ],
    )


@pytest.fixture
def form_manager(sample_form):
    return ServiceDeskFormManager(sample_form)


def test_list_fields(form_manager):
    fields = form_manager.list_fields()
    assert len(fields) == 3
    assert fields[0]["label"] == "Summary"
    assert fields[1]["id"] == "priority"
    assert fields[2]["description"] == ""


def test_list_field_values(form_manager):
    priority_values = form_manager.list_field_values("priority")
    assert len(priority_values) == 3
    assert priority_values[0]["label"] == "High"
    assert priority_values[1]["value"] == "medium"


def test_list_field_values_invalid_field(form_manager):
    with pytest.raises(
        ValueError, match="Field with identifier 'invalid_field' not found."
    ):
        form_manager.list_field_values("invalid_field")


def test_validate_valid_form(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "high",
        "description": "Test description",
    }
    assert form_manager.validate(filled_values) == True


def test_validate_missing_required_field(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "high",
    }
    with pytest.raises(ValueError, match="Missing required fields"):
        form_manager.validate(filled_values)


def test_validate_invalid_choice(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "invalid_priority",
        "description": "Test description",
    }
    with pytest.raises(
        ValueError,
        match="Invalid choice value 'invalid_priority' for field 'Priority' or 'priority'.",
    ):
        form_manager.validate(filled_values)


def test_set_field_values_valid(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "high",
        "description": "Test description",
    }
    form_filled = form_manager.set_field_values(filled_values)
    assert isinstance(form_filled, ServiceDeskFormFilled)
    assert form_filled.filled_values["summary"] == "Test summary"
    assert form_filled.filled_values["priority"] == "high"
    assert form_filled.filled_values["description"] == "Test description"


def test_set_field_values_with_labels(form_manager):
    filled_values = {
        "Summary": "Test summary",
        "Priority": "High",
        "Description": "Test description",
    }
    form_filled = form_manager.set_field_values(filled_values)
    assert form_filled.filled_values["summary"] == "Test summary"
    assert form_filled.filled_values["priority"] == "high"
    assert form_filled.filled_values["description"] == "Test description"


def test_set_field_values_invalid(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "invalid_priority",
        "description": "Test description",
    }
    with pytest.raises(ValueError):
        form_manager.set_field_values(filled_values)


def test_to_request_payload(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "high",
        "description": "Test description",
    }
    form_filled = form_manager.set_field_values(filled_values)
    payload = form_filled.to_request_payload()

    assert "summary=Test+summary" in payload
    assert "priority=high" in payload
    assert "projectId=PROJ-1" in payload
    assert "proformaFormData=" in payload


def test_create_request_payload(form_manager):
    filled_values = {
        "summary": "Test summary",
        "priority": "high",
        "description": "Test description",
    }
    payload = form_manager.create_request_payload(filled_values)

    assert payload["summary"] == "Test summary"
    assert payload["priority"] == "high"
    assert "proformaFormData" in payload


def test_convert_labels_to_ids(form_manager):
    filled_values = {
        "Summary": "Test summary",
        "Priority": "High",
        "Description": "Test description",
    }
    converted = form_manager._convert_labels_to_ids(filled_values)
    assert converted["summary"] == "Test summary"
    assert converted["priority"] == "high"
    assert converted["description"] == "Test description"


def test_convert_labels_to_ids_invalid_field(form_manager):
    filled_values = {"Invalid Field": "Test value"}
    with pytest.raises(
        ValueError, match="Field 'Invalid Field' not found in the form."
    ):
        form_manager._convert_labels_to_ids(filled_values)


def test_convert_labels_to_ids_invalid_value(form_manager):
    filled_values = {"Priority": "Invalid Priority"}
    with pytest.raises(ValueError, match="Invalid value 'Invalid Priority' for field"):
        form_manager._convert_labels_to_ids(filled_values)


if __name__ == "__main__":
    pytest.main()
