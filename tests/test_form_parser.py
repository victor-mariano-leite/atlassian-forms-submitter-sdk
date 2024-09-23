from typing import Any, Dict

import pytest

from atlassianforms.form.parser import (
    ServiceDeskForm,
    ServiceDeskFormField,
    ServiceDeskFormFieldValue,
    ServiceDeskFormParser,
)


@pytest.fixture
def sample_json_data() -> Dict[str, Any]:
    return {
        "portal": {
            "id": "PORTAL-123",
            "name": "IT Help Desk",
            "description": "IT support portal",
            "serviceDeskId": "SD-456",
            "projectId": "PROJ-789",
        },
        "reqCreate": {
            "id": "REQ-001",
            "form": {
                "name": "IT Support Request",
                "descriptionHtml": "<p>Submit your IT support request</p>",
            },
            "fields": [
                {
                    "fieldType": "text",
                    "fieldId": "summary",
                    "label": "Summary",
                    "description": "Brief description of the issue",
                    "descriptionHtml": "<p>Brief description of the issue</p>",
                    "required": True,
                    "displayed": True,
                },
                {
                    "fieldType": "textarea",
                    "fieldId": "description",
                    "label": "Description",
                    "description": "Detailed description of the issue",
                    "descriptionHtml": "<p>Detailed description of the issue</p>",
                    "required": True,
                    "displayed": True,
                    "rendererType": "wiki",
                },
                {
                    "fieldType": "select",
                    "fieldId": "priority",
                    "label": "Priority",
                    "description": "Issue priority",
                    "descriptionHtml": "<p>Issue priority</p>",
                    "required": True,
                    "displayed": True,
                    "values": [
                        {"value": "high", "label": "High", "selected": False},
                        {"value": "medium", "label": "Medium", "selected": True},
                        {"value": "low", "label": "Low", "selected": False},
                    ],
                },
            ],
            "proformaTemplateForm": {
                "updated": "2023-09-15T12:00:00Z",
                "design": {
                    "settings": {
                        "templateId": 123,
                        "templateFormUuid": "FORM-UUID-456",
                    },
                    "questions": {
                        "CUSTOM-001": {
                            "type": "text",
                            "label": "Custom Field",
                            "description": "A custom field",
                            "validation": {"rq": True},
                            "jiraField": "customfield_10001",
                        }
                    },
                },
                "proformaFieldOptions": {
                    "fields": {
                        "customfield_10001": [
                            {"id": "option1", "label": "Option 1"},
                            {"id": "option2", "label": "Option 2"},
                        ]
                    }
                },
            },
        },
        "xsrfToken": "TOKEN-789",
    }


def test_parse_service_desk_form(sample_json_data):
    form = ServiceDeskFormParser.parse(sample_json_data)

    assert isinstance(form, ServiceDeskForm)
    assert form.id == "PORTAL-123"
    assert form.service_desk_id == "SD-456"
    assert form.request_type_id == "REQ-001"
    assert form.project_id == "PROJ-789"
    assert form.portal_name == "IT Help Desk"
    assert form.portal_description == "IT support portal"
    assert form.form_name == "IT Support Request"
    assert form.form_description_html == "<p>Submit your IT support request</p>"
    assert form.updated_at == "2023-09-15T12:00:00Z"
    assert form.template_id == 123
    assert form.template_form_uuid == "FORM-UUID-456"
    assert form.atl_token == "TOKEN-789"


def test_parse_standard_fields(sample_json_data):
    form = ServiceDeskFormParser.parse(sample_json_data)

    assert len(form.fields) == 4  # 3 standard fields + 1 proforma field

    summary_field = next(field for field in form.fields if field.field_id == "summary")
    assert summary_field.field_type == "text"
    assert summary_field.label == "Summary"
    assert summary_field.required == True

    description_field = next(
        field for field in form.fields if field.field_id == "description"
    )
    assert description_field.field_type == "textarea"
    assert description_field.renderer_type == "wiki"

    priority_field = next(
        field for field in form.fields if field.field_id == "priority"
    )
    assert priority_field.field_type == "select"
    assert len(priority_field.values) == 3
    assert priority_field.values[1].value == "medium"
    assert priority_field.values[1].selected == True


def test_parse_proforma_field(sample_json_data):
    form = ServiceDeskFormParser.parse(sample_json_data)

    proforma_field = next(field for field in form.fields if field.is_proforma_field)
    assert proforma_field.field_type == "text"
    assert proforma_field.field_id == "customfield_10001"
    assert proforma_field.label == "Custom Field"
    assert proforma_field.required == True
    assert proforma_field.proforma_question_id == "CUSTOM-001"
    assert len(proforma_field.values) == 2
    assert proforma_field.values[0].value == "option1"
    assert proforma_field.values[1].label == "Option 2"


def test_parse_cascadingselect_field():
    cascading_json = {
        "portal": {
            "id": "PORTAL-123",
            "name": "Test Portal",
            "serviceDeskId": "SD-456",
            "projectId": "PROJ-789",
        },
        "reqCreate": {
            "id": "REQ-001",
            "form": {"name": "Test Form", "descriptionHtml": ""},
            "fields": [
                {
                    "fieldType": "cascadingselect",
                    "fieldId": "cascading",
                    "label": "Cascading Select",
                    "required": True,
                    "displayed": True,
                    "values": [
                        {
                            "value": "parent1",
                            "label": "Parent 1",
                            "children": [
                                {"value": "child1", "label": "Child 1"},
                                {"value": "child2", "label": "Child 2"},
                            ],
                        },
                        {
                            "value": "parent2",
                            "label": "Parent 2",
                            "children": [{"value": "child3", "label": "Child 3"}],
                        },
                    ],
                }
            ],
        },
    }

    form = ServiceDeskFormParser.parse(cascading_json)

    assert len(form.fields) == 2  # Main field + subfield

    main_field = form.fields[0]
    assert main_field.field_type == "cascadingselect"
    assert main_field.field_id == "cascading"
    assert len(main_field.values) == 2
    assert len(main_field.values[0].children) == 2
    assert len(main_field.values[1].children) == 1

    subfield = form.fields[1]
    assert subfield.field_id == "cascading:1"
    assert subfield.label == "Cascading Select (Subfield)"
    assert subfield.depends_on == "cascading"


if __name__ == "__main__":
    pytest.main()
