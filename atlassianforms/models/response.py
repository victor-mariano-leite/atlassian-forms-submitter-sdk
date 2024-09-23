from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Reporter:
    email: str
    display_name: str
    avatar_url: str
    account_id: str


@dataclass
class IssueField:
    id: str
    label: str
    value: Dict


@dataclass
class Issue:
    id: int
    key: str
    reporter: Reporter
    participants: List[str]
    organisations: List[str]
    sequence: int
    service_desk_key: str
    request_type_name: str
    request_type_id: int
    summary: str
    is_new: bool
    status: str
    date: str
    friendly_date: str
    fields: List[IssueField]
    activity_stream: List[str] = field(default_factory=list)
    request_icon: int = 0
    icon_url: str = ""
    can_browse: bool = True
    can_attach: bool = True
    category_key: str = ""
    creator_account_id: str = ""
    form_key: str = ""


@dataclass
class CreateRequestResponse:
    reporter: Reporter
    request_type_name: str
    key: str
    issue_type: str
    issue_type_name: str
    issue: Issue
    can_create_issues: bool
    can_add_comment: bool
    issue_link_url: str
    request_details_base_url: str


class CreateRequestResponseParser:
    """
    Parser class to convert JSON response into CreateRequestResponse dataclass.

    Methods
    -------
    parse(data: Dict) -> CreateRequestResponse
        Parses the JSON data into a CreateRequestResponse object.
    _parse_reporter(reporter_data: Dict) -> Reporter
        Parses the reporter information.
    _parse_issue_field(field_data: Dict) -> IssueField
        Parses a single issue field.
    _parse_issue(issue_data: Dict) -> Issue
        Parses the issue information.
    """

    @staticmethod
    def parse(data: Dict) -> CreateRequestResponse:
        """
        Parses the JSON data into a CreateRequestResponse object.

        Parameters
        ----------
        data : Dict
            The JSON data to parse.

        Returns
        -------
        CreateRequestResponse
            The parsed CreateRequestResponse object.
        """
        reporter = CreateRequestResponseParser._parse_reporter(data["reporter"])
        issue = CreateRequestResponseParser._parse_issue(data["issue"])

        return CreateRequestResponse(
            reporter=reporter,
            request_type_name=data.get("requestTypeName", ""),
            key=data.get("key", ""),
            issue_type=data.get("issueType", ""),
            issue_type_name=data.get("issueTypeName", ""),
            issue=issue,
            can_create_issues=data.get("canCreateIssues", False),
            can_add_comment=data.get("canAddComment", False),
            issue_link_url=data.get("issueLinkUrl", ""),
            request_details_base_url=data.get("requestDetailsBaseUrl", ""),
        )

    @staticmethod
    def _parse_reporter(reporter_data: Dict) -> Reporter:
        """
        Parses the reporter information.

        Parameters
        ----------
        reporter_data : Dict
            The reporter data to parse.

        Returns
        -------
        Reporter
            The parsed Reporter object.
        """
        return Reporter(
            email=reporter_data.get("email", ""),
            display_name=reporter_data.get("displayName", ""),
            avatar_url=reporter_data.get("avatarUrl", ""),
            account_id=reporter_data.get("accountId", ""),
        )

    @staticmethod
    def _parse_issue_field(field_data: Dict) -> IssueField:
        """
        Parses a single issue field.

        Parameters
        ----------
        field_data : Dict
            The issue field data to parse.

        Returns
        -------
        IssueField
            The parsed IssueField object.
        """
        return IssueField(
            id=field_data.get("id", ""),
            label=field_data.get("label", ""),
            value=field_data.get("value", {}),
        )

    @staticmethod
    def _parse_issue(issue_data: Dict) -> Issue:
        """
        Parses the issue information.

        Parameters
        ----------
        issue_data : Dict
            The issue data to parse.

        Returns
        -------
        Issue
            The parsed Issue object.
        """
        reporter = CreateRequestResponseParser._parse_reporter(issue_data["reporter"])
        fields = [
            CreateRequestResponseParser._parse_issue_field(f)
            for f in issue_data.get("fields", [])
        ]

        return Issue(
            id=issue_data.get("id", 0),
            key=issue_data.get("key", ""),
            reporter=reporter,
            participants=issue_data.get("participants", []),
            organisations=issue_data.get("organisations", []),
            sequence=issue_data.get("sequence", 0),
            service_desk_key=issue_data.get("serviceDeskKey", ""),
            request_type_name=issue_data.get("requestTypeName", ""),
            request_type_id=issue_data.get("requestTypeId", 0),
            summary=issue_data.get("summary", ""),
            is_new=issue_data.get("isNew", False),
            status=issue_data.get("status", ""),
            date=issue_data.get("date", ""),
            friendly_date=issue_data.get("friendlyDate", ""),
            fields=fields,
            activity_stream=issue_data.get("activityStream", []),
            request_icon=issue_data.get("requestIcon", 0),
            icon_url=issue_data.get("iconUrl", ""),
            can_browse=issue_data.get("canBrowse", True),
            can_attach=issue_data.get("canAttach", True),
            category_key=issue_data.get("categoryKey", ""),
            creator_account_id=issue_data.get("creatorAccountId", ""),
            form_key=issue_data.get("formKey", ""),
        )
