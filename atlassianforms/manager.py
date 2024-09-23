import base64
from typing import Any, Dict, List

import requests
from atlassian import Jira, ServiceDesk

from atlassianforms.form.manager import ServiceDeskFormFilled


class ServiceDeskRequestError(Exception):
    """
    Custom exception class for errors related to Service Desk requests.

    Attributes
    ----------
    status_code : int
        The HTTP status code returned by the failed request.
    error_message : str
        The error message returned by the failed request.

    Methods
    -------
    __str__():
        Returns a formatted string representation of the error.
    """

    def __init__(self, status_code: int, error_message: str):
        """
        Initializes the ServiceDeskRequestError with the status code and error message.

        Parameters
        ----------
        status_code : int
            The HTTP status code returned by the failed request.
        error_message : str
            The error message returned by the failed request.
        """
        self.status_code = status_code
        self.error_message = error_message
        super().__init__(self.__str__())

    def __str__(self):
        """
        Returns a formatted string representation of the error.

        Returns
        -------
        str
            A string representation of the error.
        """
        return f"ServiceDeskRequestError: {self.status_code} - {self.error_message}"


def remove_disposable_keys(data, disposable_keys):
    """
    Recursively removes the disposable keys from a dictionary or list.

    Parameters
    ----------
    data : dict or list
        The JSON data (as a dict or list) from which keys should be removed.
    disposable_keys : list
        A list of keys to be removed from the data.

    Returns
    -------
    dict or list
        The cleaned-up data with disposable keys removed.
    """
    if isinstance(data, dict):
        return {
            k: remove_disposable_keys(v, disposable_keys)
            for k, v in data.items()
            if k not in disposable_keys
        }
    elif isinstance(data, list):
        return [remove_disposable_keys(item, disposable_keys) for item in data]
    else:
        return data


def clean_response(response):
    """
    Cleans up the JSON response by removing unnecessary keys.

    Parameters
    ----------
    response : dict
        The JSON response to clean.

    Returns
    -------
    dict
        The cleaned response.
    """
    disposable_keys = [
        "key",
        "portalBaseUrl",
        "onlyPortal",
        "createPermission",
        "portalAnnouncement",
        "canViewCreateRequestForm",
        "isProjectSimplified",
        "mediaApiUploadInformation",
        "userLanguageHeader",
        "userLanguageMessageWiki",
        "defaultLanguageHeader",
        "defaultLanguageMessage",
        "defaultLanguageDisplayName",
        "isUsingLanguageSupport",
        "translations",
        "callToAction",
        "intro",
        "instructions",
        "icon",
        "iconUrl",
        "userOrganisations",
        "canBrowseUsers",
        "requestCreateBaseUrl",
        "requestValidateBaseUrl",
        "calendarParams",
        "kbs",
        "canRaiseOnBehalf",
        "canSignupCustomers",
        "canCreateAttachments",
        "attachmentRequiredField",
        "hasGroups",
        "canSubmitWithEmailAddress",
        "showRecaptcha",
        "siteKey",
        "hasProformaForm",
        "linkedJiraFields",
        "portalWebFragments",
        "headerPanels",
        "subheaderPanels",
        "footerPanels",
        "pagePanels",
        "localId",
    ]

    return remove_disposable_keys(response, disposable_keys)


class ServiceDeskManager:
    """
    A class to manage interactions with the Atlassian Service Desk API and to fetch
    request parameters necessary for creating service desk requests.

    Attributes
    ----------
    base_url : str
        The base URL for the Atlassian account.
    username : str
        The username for authentication.
    auth_token : str
        The authentication token or password.
    service_desk : ServiceDesk
        An instance of the Atlassian ServiceDesk client.
    jira : Jira
        An instance of the Atlassian Jira client.

    Methods
    -------
    get_service_desks() -> List[Dict]:
        Fetches and returns all service desk projects.
    get_request_types(portal_id: int) -> List[Dict]:
        Fetches and returns all request types for a specific service desk project.
    fetch_form(portal_id: int, request_type_id: int) -> Dict:
        Fetches the fields and parameters for the specified service desk request type.
    validate_field_data(portal_id: int, request_type_id: int, field_data: dict) -> bool:
        Validates the provided field data against the required fields from the request parameters.
    create_service_desk_request(request_type: str, reporter_email: str,
                                field_data: dict, portal_id: str) -> Dict:
        Creates a service desk request with the specified parameters.
    """

    def __init__(self, base_url: str, username: str, auth_token: str):
        """
        Initializes the ServiceDeskManager class with authentication details.

        Parameters
        ----------
        base_url : str
            The base URL for the Atlassian account.
        username : str
            The username for authentication.
        auth_token : str
            The authentication token or password.
        """
        self.base_url = base_url
        self.username = username
        self.auth_token = auth_token
        self.auth_header = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{auth_token}'.encode()).decode()}",
            "X-Atlassian-Token": "no-check",
        }
        self.default_headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "x-requested-with": "XMLHttpRequest",
        }
        self.all_headers = {**self.default_headers, **self.auth_header}
        self.service_desk = ServiceDesk(
            url=base_url, username=username, password=auth_token
        )
        self.jira = Jira(url=base_url, username=username, password=auth_token)

    def get_service_desks(self) -> List[Dict]:
        """
        Fetches and returns all service desk projects.

        Returns
        -------
        List[Dict]
            A list of dictionaries containing service desk project details.
        """
        return self.service_desk.get_service_desks()

    def get_request_types(self, service_desk_id: int, group_id: int) -> List[Dict]:
        """
        Fetches and returns all request types for a specific service desk project.

        Parameters
        ----------
        service_desk_id : int
            The ID of the service desk project.
        group_id : int
            The ID of the group.

        Returns
        -------
        List[Dict]
            A list of dictionaries containing request type details.
        """
        return self.service_desk.get_request_types(
            service_desk_id=service_desk_id, group_id=group_id
        )

    def fetch_form(self, portal_id: int, request_type_id: int) -> Dict:
        """
        Fetches the fields and parameters for the specified service desk request type,
        including additional options for Proforma fields if they exist.

        Parameters
        ----------
        portal_id : int
            The ID of the service desk project (portalId).
        request_type_id : int
            The ID of the request type.

        Returns
        -------
        Dict
            The cleaned JSON response containing the fields, parameters, and additional options.
        """
        form_data = self._fetch_form_data(portal_id, request_type_id)
        additional_options = self._fetch_proforma_options(portal_id, request_type_id)
        autocomplete_options = self._fetch_autocomplete_options(form_data)
        form_data["reqCreate"]["proformaTemplateForm"][
            "proformaFieldOptions"
        ] = additional_options
        form_data["reqCreate"]["autocompleteOptions"] = autocomplete_options
        return form_data

    def _fetch_form_data(self, portal_id: int, request_type_id: int) -> Dict:
        """
        Fetches the form data for the specified service desk request type.

        Parameters
        ----------
        portal_id : int
            The ID of the service desk project (portalId).
        request_type_id : int
            The ID of the request type.

        Returns
        -------
        Dict
            The JSON response containing the fields and parameters.
        """
        url = f"{self.base_url}/rest/servicedesk/1/customer/models"
        headers = self.all_headers
        body = {
            "options": {
                "portalWebFragments": {
                    "portalId": portal_id,
                    "requestTypeId": request_type_id,
                    "portalPage": "CREATE_REQUEST",
                },
                "portal": {"id": portal_id},
                "reqCreate": {"portalId": portal_id, "id": request_type_id},
                "portalId": portal_id,
            },
            "models": ["portalWebFragments", "portal", "reqCreate"],
            "context": {
                "helpCenterAri": "ari:cloud:help::help-center/023eca6c-913d-41af-a182-61e86fd72ccc/de1070f9-b9dd-460c-b02f-104fc367db40",
                "clientBasePath": f"{self.base_url}/servicedesk/customer",
            },
        }
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()

        return clean_response(
            {**response.json(), "portalId": portal_id, "requestTypeId": request_type_id}
        )

    def _fetch_proforma_options(self, portal_id: int, request_type_id: int) -> Dict:
        """
        Fetches additional options for Proforma fields using a separate API endpoint.

        Parameters
        ----------
        portal_id : int
            The ID of the service desk project (portalId).
        request_type_id : int
            The ID of the request type.

        Returns
        -------
        Dict
            A dictionary containing the additional Proforma field options.
        """
        try:
            headers = self.all_headers
            tenant_info_url = f"{self.base_url}/_edge/tenant_info"
            tenant_info_response = requests.get(tenant_info_url, headers=headers)
            tenant_info_response.raise_for_status()
            cloud_id = tenant_info_response.json()["cloudId"]

            form_choices_url = f"{self.base_url}/gateway/api/proforma/portal/cloudid/{cloud_id}/api/3/portal/{portal_id}/requesttype/{request_type_id}/formchoices"
            form_choices_response = requests.get(form_choices_url, headers=headers)
            form_choices_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return {}
        return form_choices_response.json()

    def _fetch_autocomplete_options(self, form_data: dict) -> List[Dict[Any, Any]]:
        """
        Fetches autocomplete options for a specific field in a service desk request form.

        Parameters
        ----------
        portal_id : int
            The ID of the service desk project (portalId).
        request_id : int
            The ID of the specific service desk request.
        customfield_id : str
            The ID of the custom field for which autocomplete options are being fetched.

        Returns
        -------
        Dict
            A dictionary containing the autocomplete options for the specified custom field.
        """
        # TODO: discover how to paginate the request, since there is a hasNextPage field in the response
        portal_id = form_data["portalId"]
        request_id = form_data["reqCreate"]["id"]
        field_map = {"fieldValueMap": {}, "query": ""}
        field_map_values = {
            field["fieldId"]: "" for field in form_data["reqCreate"]["fields"]
        }
        field_map["fieldValueMap"] = field_map_values
        autocomplete_fields = [
            field
            for field in form_data["reqCreate"]["fields"]
            if field.get("autoCompleteUrl", "")
            and field.get("fieldType") != "organisationpicker"
        ]
        additional_options = []
        for field in autocomplete_fields:
            customfield_id = field["fieldId"]
            try:
                headers = self.all_headers
                autocomplete_url = f"{self.base_url}/rest/servicedesk/cmdb/1/customer/portal/{portal_id}/request/{request_id}/field/{customfield_id}/autocomplete"
                response = requests.post(
                    autocomplete_url, headers=headers, json=field_map
                )
                response.raise_for_status()
                response_dict = response.json()
            except requests.exceptions.HTTPError as e:
                print(
                    f"Failed to fetch autocomplete options for field {customfield_id}: {e}"
                )
                response_dict = {}
            response_dict = {
                **response_dict,
                "fieldId": customfield_id,
                "fieldType": field.get("fieldType", ""),
                "fieldLabel": field.get("label", ""),
                "fieldDescription": field.get("description", ""),
                "fieldRequired": field.get("required", ""),
                "fieldDisplayed": field.get("displayed", ""),
                "fieldPresetValues": field.get("presetValues", ""),
            }
            additional_options.append(response_dict)
        return additional_options

    def create_request(self, form_filled: ServiceDeskFormFilled) -> Dict:
        """
        Creates a service desk request with the specified parameters.

        Parameters
        ----------
        form_filled : ServiceDeskFormFilled
            An instance of ServiceDeskFormFilled containing validated user input.
        reporter_email : str
            The email of the reporter.

        Returns
        -------
        Dict
            The response from the API after creating the request.
        """
        field_data = form_filled.to_request_payload()

        portal_id = form_filled.form.service_desk_id
        request_type_id = form_filled.form.request_type_id

        url = f"{self.base_url}/servicedesk/customer/portal/{portal_id}/create/{request_type_id}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            **self.auth_header,
        }

        params = requests.models.RequestEncodingMixin._encode_params(field_data)
        response = requests.post(url, headers=headers, data=params)

        if response.status_code in (201, 200):
            return response.json()
        else:
            raise ServiceDeskRequestError(response.status_code, response.text)
