from datetime import datetime
from typing import Any, Dict

import pytest

from atlassianforms.form.parser import (
    ServiceDeskForm,
    ServiceDeskFormField,
    ServiceDeskFormFieldValue,
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
        fields=[
            ServiceDeskFormField(
                field_type="dt",
                field_id="date_field",
                label="Date Field",
                required=True,
                displayed=True,
                field_config_id="date_config",
                description="Date field description",
                description_html="<p>Date field description</p>",
            ),
            ServiceDeskFormField(
                field_type="select",
                field_id="select_field",
                label="Select Field",
                required=True,
                displayed=True,
                field_config_id="select_config",
                description="Select field description",
                description_html="<p>Select field description</p>",
                values=[
                    ServiceDeskFormFieldValue(value="option1", label="Option 1"),
                    ServiceDeskFormFieldValue(value="option2", label="Option 2"),
                ],
            ),
            ServiceDeskFormField(
                field_type="text",
                field_id="text_field",
                label="Text Field",
                required=True,
                displayed=True,
                field_config_id="text_config",
                description="Text field description",
                description_html="<p>Text field description</p>",
            ),
            ServiceDeskFormField(
                field_type="adf",
                field_id="adf_field",
                label="ADF Field",
                required=True,
                displayed=True,
                field_config_id="adf_config",
                description="ADF field description",
                description_html="<p>ADF field description</p>",
            ),
        ],
    )


@pytest.fixture
def validator():
    return ServiceDeskFormValidator()


def test_validate_valid_form(sample_form, validator):
    filled_values = {
        "date_field": "2023-05-15T10:30",
        "select_field": "option1",
        "text_field": "Sample text",
        "adf_field": '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Sample ADF"}]}]}',
    }
    validator.validate(filled_values, sample_form)  # Should not raise any exception


def test_validate_invalid_date(sample_form, validator):
    filled_values = {"date_field": "invalid-date"}
    with pytest.raises(ValueError, match="Invalid date-time value"):
        validator.validate(filled_values, sample_form)


def test_validate_invalid_select(sample_form, validator):
    filled_values = {"select_field": "invalid-option"}
    with pytest.raises(ValueError, match="Invalid choice value"):
        validator.validate(filled_values, sample_form)


def test_validate_invalid_text(sample_form, validator):
    filled_values = {"text_field": 12345}  # Not a string
    with pytest.raises(ValueError, match="Invalid text value"):
        validator.validate(filled_values, sample_form)


def test_validate_invalid_adf(sample_form, validator):
    filled_values = {"adf_field": '{"invalid": "json"}'}
    with pytest.raises(ValueError, match="Invalid ADF value"):
        validator.validate(filled_values, sample_form)


def test_validate_missing_field(sample_form, validator):
    filled_values = {"non_existent_field": "value"}
    with pytest.raises(
        ValueError, match="Field 'non_existent_field' not found in the form"
    ):
        validator.validate(filled_values, sample_form)


def test_validate_dt_field(sample_form, validator):
    assert validator._validate_dt("2023-05-15T10:30") == True
    assert validator._validate_dt("invalid-date") == False


def test_validate_choice_field(sample_form, validator):
    choices = ["option1", "option2"]
    assert validator._validate_choice("option1", choices) == True
    assert validator._validate_choice("invalid", choices) == False


def test_validate_text_field(sample_form, validator):
    assert validator._validate_text("Valid text") == True
    assert validator._validate_text(12345) == False


def test_validate_adf_field(sample_form, validator):
    valid_adf = '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Valid ADF"}]}]}'
    invalid_adf = '{"invalid": "json"}'
    assert validator._validate_adf(valid_adf) == True
    assert validator._validate_adf(invalid_adf) == False


def test_get_field_by_id_or_label(sample_form, validator):
    assert validator._get_field_by_id_or_label(sample_form, "date_field") is not None
    assert validator._get_field_by_id_or_label(sample_form, "Date Field") is not None
    assert validator._get_field_by_id_or_label(sample_form, "non_existent") is None


def test_get_value_by_label_or_id(sample_form, validator):
    values = sample_form.fields[1].values  # select_field values
    assert validator._get_value_by_label_or_id(values, "option1") is not None
    assert validator._get_value_by_label_or_id(values, "Option 1") is not None
    assert validator._get_value_by_label_or_id(values, "non_existent") is None


if __name__ == "__main__":
    pytest.main()
