from typing import Any, Dict

from atlassianforms.form.manager import ServiceDeskFormManager
from atlassianforms.form.parser import ServiceDeskFormParser
from atlassianforms.manager import ServiceDeskManager
from atlassianforms.models.response import CreateRequestResponseParser

FORM_DIDNT_FETCH_ERROR = (
    "Form has not been fetched and parsed. Please run `fetch_and_parse_form` first."
)


class ServiceDeskFormClient:
    """
    A client class for interacting with Atlassian Service Desk forms.

    This class provides utilities to fetch forms, parse them, manage form fields, and create service desk requests.

    Attributes
    ----------
    base_url : str
        The base URL of the Atlassian Service Desk.
    username : str
        The username used for authentication.
    auth_token : str
        The authentication token.
    service_desk_manager : ServiceDeskManager
        An instance of ServiceDeskManager for managing service desk requests.
    form_manager : ServiceDeskFormManager
        An instance of ServiceDeskFormManager for managing form fields and values.

    Methods
    -------
    fetch_and_parse_form(portal_id: int, request_type_id: int) -> None
        Fetches and parses the form for the given portal and request type ID.
    list_fields() -> None
        Lists all fields in the form.
    list_field_values(field_name: str) -> None
        Lists possible values for a specific field in the form.
    set_form_values(values: Dict[str, Any]) -> Dict[str, Any]
        Sets the values for the form fields.
    create_request(filled_values: Dict[str, Any]) -> CreateRequestResponseParser
        Creates a service desk request with the filled form values.
    """

    def __init__(self, base_url: str, username: str, auth_token: str) -> None:
        """
        Initializes the ServiceDeskFormClient with the provided credentials.

        Parameters
        ----------
        base_url : str
            The base URL of the Atlassian Service Desk.
        username : str
            The username used for authentication.
        auth_token : str
            The authentication token.
        """
        self.base_url = base_url
        self.username = username
        self.auth_token = auth_token
        self.service_desk_manager = ServiceDeskManager(
            base_url=self.base_url, username=self.username, auth_token=self.auth_token
        )
        self.form_manager = None

    def fetch_and_parse_form(self, portal_id: int, request_type_id: int) -> None:
        """
        Fetches and parses the form for the given portal and request type ID.

        Parameters
        ----------
        portal_id : int
            The ID of the service desk portal.
        request_type_id : int
            The ID of the request type.
        """
        form = self.service_desk_manager.fetch_form(
            portal_id=portal_id, request_type_id=request_type_id
        )
        form_obj = ServiceDeskFormParser.parse(form)
        self.form_manager = ServiceDeskFormManager(form_obj)

    def list_fields(self) -> None:
        """
        Lists all fields in the fetched form.

        Raises
        ------
        ValueError
            If the form has not been fetched and parsed.
        """
        if self.form_manager is None:
            raise ValueError(FORM_DIDNT_FETCH_ERROR)
        self.form_manager.list_fields()

    def list_field_values(self, field_name: str) -> None:
        """
        Lists possible values for a specific field in the form.

        Parameters
        ----------
        field_name : str
            The name of the field to list values for.

        Raises
        ------
        ValueError
            If the form has not been fetched and parsed.
        """
        if self.form_manager is None:
            raise ValueError(FORM_DIDNT_FETCH_ERROR)
        self.form_manager.list_field_values(field_name)

    def set_form_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sets the values for the form fields.

        Parameters
        ----------
        values : Dict[str, Any]
            A dictionary where the keys are field names and the values are the values to set for the fields.

        Returns
        -------
        Dict[str, Any]
            The filled form ready to be submitted as a request.

        Raises
        ------
        ValueError
            If the form has not been fetched and parsed.
        """
        if self.form_manager is None:
            raise ValueError(FORM_DIDNT_FETCH_ERROR)
        return self.form_manager.set_field_values(values)

    def create_request(
        self, filled_values: Dict[str, Any]
    ) -> CreateRequestResponseParser:
        """
        Creates a service desk request with the filled form values.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The filled form values.

        Returns
        -------
        CreateRequestResponseParser
            The response of the create request parsed into a CreateRequestResponseParser object.
        """
        response_dict = self.service_desk_manager.create_request(filled_values)
        return CreateRequestResponseParser.parse(response_dict)
