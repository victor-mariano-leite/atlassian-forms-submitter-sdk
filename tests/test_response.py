import pytest

from atlassianforms.models.response import (
    CreateRequestResponse,
    CreateRequestResponseParser,
    Issue,
    IssueField,
    Reporter,
)


@pytest.fixture
def sample_response_data():
    return {
        "reporter": {
            "email": "john.doe@example.com",
            "displayName": "John Doe",
            "avatarUrl": "https://example.com/avatar.jpg",
            "accountId": "12345",
        },
        "requestTypeName": "IT Support",
        "key": "IT-123",
        "issueType": "10000",
        "issueTypeName": "Service Request",
        "issue": {
            "id": 123,
            "key": "IT-123",
            "reporter": {
                "email": "john.doe@example.com",
                "displayName": "John Doe",
                "avatarUrl": "https://example.com/avatar.jpg",
                "accountId": "12345",
            },
            "participants": ["user1", "user2"],
            "organisations": ["org1", "org2"],
            "sequence": 1,
            "serviceDeskKey": "SD-1",
            "requestTypeName": "IT Support",
            "requestTypeId": 10,
            "summary": "Need help with printer",
            "isNew": True,
            "status": "Open",
            "date": "2023-05-15T10:30:00Z",
            "friendlyDate": "Today",
            "fields": [
                {
                    "id": "summary",
                    "label": "Summary",
                    "value": {"text": "Need help with printer"},
                },
                {
                    "id": "description",
                    "label": "Description",
                    "value": {"text": "Printer not responding"},
                },
            ],
            "activityStream": ["Activity 1", "Activity 2"],
            "requestIcon": 1,
            "iconUrl": "https://example.com/icon.png",
            "canBrowse": True,
            "canAttach": True,
            "categoryKey": "printer",
            "creatorAccountId": "12345",
            "formKey": "FORM-1",
        },
        "canCreateIssues": True,
        "canAddComment": True,
        "issueLinkUrl": "https://example.com/issues/IT-123",
        "requestDetailsBaseUrl": "https://example.com/requests/",
    }


def test_parse_reporter():
    reporter_data = {
        "email": "john.doe@example.com",
        "displayName": "John Doe",
        "avatarUrl": "https://example.com/avatar.jpg",
        "accountId": "12345",
    }
    reporter = CreateRequestResponseParser._parse_reporter(reporter_data)
    assert isinstance(reporter, Reporter)
    assert reporter.email == "john.doe@example.com"
    assert reporter.display_name == "John Doe"
    assert reporter.avatar_url == "https://example.com/avatar.jpg"
    assert reporter.account_id == "12345"


def test_parse_issue_field():
    field_data = {
        "id": "summary",
        "label": "Summary",
        "value": {"text": "Need help with printer"},
    }
    issue_field = CreateRequestResponseParser._parse_issue_field(field_data)
    assert isinstance(issue_field, IssueField)
    assert issue_field.id == "summary"
    assert issue_field.label == "Summary"
    assert issue_field.value == {"text": "Need help with printer"}


def test_parse_issue(sample_response_data):
    issue_data = sample_response_data["issue"]
    issue = CreateRequestResponseParser._parse_issue(issue_data)
    assert isinstance(issue, Issue)
    assert issue.id == 123
    assert issue.key == "IT-123"
    assert isinstance(issue.reporter, Reporter)
    assert issue.participants == ["user1", "user2"]
    assert issue.organisations == ["org1", "org2"]
    assert issue.sequence == 1
    assert issue.service_desk_key == "SD-1"
    assert issue.request_type_name == "IT Support"
    assert issue.request_type_id == 10
    assert issue.summary == "Need help with printer"
    assert issue.is_new is True
    assert issue.status == "Open"
    assert issue.date == "2023-05-15T10:30:00Z"
    assert issue.friendly_date == "Today"
    assert len(issue.fields) == 2
    assert all(isinstance(field, IssueField) for field in issue.fields)
    assert issue.activity_stream == ["Activity 1", "Activity 2"]
    assert issue.request_icon == 1
    assert issue.icon_url == "https://example.com/icon.png"
    assert issue.can_browse is True
    assert issue.can_attach is True
    assert issue.category_key == "printer"
    assert issue.creator_account_id == "12345"
    assert issue.form_key == "FORM-1"


def test_parse_create_request_response(sample_response_data):
    response = CreateRequestResponseParser.parse(sample_response_data)
    assert isinstance(response, CreateRequestResponse)
    assert isinstance(response.reporter, Reporter)
    assert response.request_type_name == "IT Support"
    assert response.key == "IT-123"
    assert response.issue_type == "10000"
    assert response.issue_type_name == "Service Request"
    assert isinstance(response.issue, Issue)
    assert response.can_create_issues is True
    assert response.can_add_comment is True
    assert response.issue_link_url == "https://example.com/issues/IT-123"
    assert response.request_details_base_url == "https://example.com/requests/"


def test_parse_with_missing_optional_fields():
    minimal_data = {
        "reporter": {
            "email": "john.doe@example.com",
            "displayName": "John Doe",
            "avatarUrl": "https://example.com/avatar.jpg",
            "accountId": "12345",
        },
        "issue": {
            "id": 123,
            "key": "IT-123",
            "reporter": {
                "email": "john.doe@example.com",
                "displayName": "John Doe",
                "avatarUrl": "https://example.com/avatar.jpg",
                "accountId": "12345",
            },
            "summary": "Minimal issue",
        },
    }
    response = CreateRequestResponseParser.parse(minimal_data)
    assert isinstance(response, CreateRequestResponse)
    assert response.request_type_name == ""
    assert response.can_create_issues is False
    assert response.can_add_comment is False
    assert response.issue_link_url == ""
    assert response.request_details_base_url == ""
    assert response.issue.participants == []
    assert response.issue.organisations == []
    assert response.issue.sequence == 0
    assert response.issue.fields == []


def test_parse_with_empty_fields():
    data_with_empty_fields = {
        "reporter": {},
        "issue": {
            "reporter": {},
            "fields": [{"id": "empty_field"}, {"label": "Empty Label"}, {"value": {}}],
        },
    }
    response = CreateRequestResponseParser.parse(data_with_empty_fields)
    assert isinstance(response, CreateRequestResponse)
    assert response.reporter.email == ""
    assert response.reporter.display_name == ""
    assert response.reporter.avatar_url == ""
    assert response.reporter.account_id == ""
    assert len(response.issue.fields) == 3
    assert response.issue.fields[0].id == "empty_field"
    assert response.issue.fields[0].label == ""
    assert response.issue.fields[0].value == {}
    assert response.issue.fields[1].id == ""
    assert response.issue.fields[1].label == "Empty Label"
    assert response.issue.fields[1].value == {}
    assert response.issue.fields[2].id == ""
    assert response.issue.fields[2].label == ""
    assert response.issue.fields[2].value == {}


if __name__ == "__main__":
    pytest.main()
