from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ServiceDeskFormFieldValue:
    """
    Data class representing a value within a Service Desk form field.

    Attributes
    ----------
    value : str
        The value identifier.
    label : str
        The label associated with this value.
    selected : bool
        Whether this value is pre-selected.
    children : List['ServiceDeskFormFieldValue']
        Child values that depend on this value.
    """

    value: str
    label: str
    selected: bool = False
    children: List["ServiceDeskFormFieldValue"] = field(default_factory=list)
    additional_data: Dict[str, Any] = field(default_factory=dict)

    def add_child(self, child_value: "ServiceDeskFormFieldValue") -> None:
        """
        Add a child value to this value.

        Parameters
        ----------
        child_value : ServiceDeskFormFieldValue
            The child value to be added.
        """
        self.children.append(child_value)

    def has_children(self) -> bool:
        """
        Check if this value has child values.

        Returns
        -------
        bool
            True if this value has children, False otherwise.
        """
        return len(self.children) > 0


@dataclass
class ServiceDeskFormField:
    """
    Data class representing a field in a Service Desk form.

    Attributes
    ----------
    field_type : str
        The type of the field (e.g., 'text', 'cascadingselect', 'textarea').
    field_id : str
        The unique identifier for the field.
    field_config_id : str
        The configuration ID for the field (may be empty).
    label : str
        The label of the field displayed in the UI.
    description : str
        A brief description of the field's purpose.
    description_html : str
        HTML-formatted description of the field.
    required : bool
        Whether the field is required or optional.
    displayed : bool
        Whether the field is displayed in the form.
    preset_values : List[Any]
        A list of preset values that may be pre-selected or pre-filled.
    values : List[ServiceDeskFormFieldValue]
        A list of possible values for this field, potentially hierarchical.
    renderer_type : Optional[str]
        The renderer type if the field is a textarea.
    auto_complete_url : Optional[str]
        The URL used for autocomplete in case of organisationpicker fields.
    depends_on : Optional[str]
        The ID of another field that this field depends on.
    children : List['ServiceDeskFormField']
        A list of child fields that depend on this field.
    is_proforma_field : bool
        Indicates whether this field is a proforma field.
    proforma_question_id : Optional[str]
        The question ID associated with this field if it's a proforma field.
    """

    field_type: str
    field_id: str
    field_config_id: str
    label: str
    description: str
    description_html: str
    required: bool
    displayed: bool
    preset_values: List[Any] = field(default_factory=list)
    values: List[ServiceDeskFormFieldValue] = field(default_factory=list)
    renderer_type: Optional[str] = None
    auto_complete_url: Optional[str] = None
    depends_on: Optional[str] = None
    children: List["ServiceDeskFormField"] = field(default_factory=list)
    is_proforma_field: bool = False
    proforma_question_id: Optional[str] = None

    def is_required(self) -> bool:
        """
        Check if the field is required.

        Returns
        -------
        bool
            True if the field is required, False otherwise.
        """
        return self.required

    def has_autocomplete(self) -> bool:
        """
        Check if the field has an autocomplete URL.

        Returns
        -------
        bool
            True if the field has an autocomplete URL, False otherwise.
        """
        return self.auto_complete_url is not None

    def add_child(self, child_field: "ServiceDeskFormField") -> None:
        """
        Add a child field to this field.

        Parameters
        ----------
        child_field : ServiceDeskFormField
            The child field to be added to this field.
        """
        self.children.append(child_field)

    def get_children(self) -> List["ServiceDeskFormField"]:
        """
        Get the list of child fields.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of child fields dependent on this field.
        """
        return self.children

    def is_dependent(self) -> bool:
        """
        Check if this field is dependent on another field.

        Returns
        -------
        bool
            True if this field has a dependency, False otherwise.
        """
        return self.depends_on is not None


@dataclass
class ServiceDeskForm:
    """
    Data class representing a Service Desk form.

    Attributes
    ----------
    portal_name : str
        The name of the portal to which the form belongs.
    portal_description : str
        A brief description of the portal's purpose.
    form_name : str
        The name of the form.
    form_description_html : str
        HTML-formatted description of the form.
    fields : List[ServiceDeskFormField]
        A list of fields that make up the form.
    updated_at : Optional[str]
        The last updated timestamp of the form.
    template_id : Optional[int]
        The ID of the template associated with the form.
    template_form_uuid : Optional[str]
        The UUID of the template form.
    """

    id: str
    service_desk_id: str
    request_type_id: str
    project_id: str
    portal_name: str
    portal_description: str
    form_name: str
    form_description_html: str
    fields: List[ServiceDeskFormField] = field(default_factory=list)
    updated_at: Optional[str] = None
    template_id: Optional[int] = None
    template_form_uuid: Optional[str] = None
    atl_token: Optional[str] = None

    def add_field(self, field: ServiceDeskFormField) -> None:
        """
        Add a new field to the form.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field to be added to the form.
        """
        self.fields.append(field)

    def get_required_fields(self) -> List[ServiceDeskFormField]:
        """
        Get a list of all required fields in the form.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of required fields.
        """
        return [field for field in self.fields if field.is_required()]

    def get_field_by_id(self, field_id: str) -> Optional[ServiceDeskFormField]:
        """
        Get a field by its ID.

        Parameters
        ----------
        field_id : str
            The ID of the field to retrieve.

        Returns
        -------
        Optional[ServiceDeskFormField]
            The field with the given ID, or None if not found.
        """
        return next(
            (field for field in self.fields if field.field_id == field_id), None
        )

    def has_autocomplete_fields(self) -> bool:
        """
        Check if the form contains any fields with autocomplete functionality.

        Returns
        -------
        bool
            True if any field in the form has autocomplete, False otherwise.
        """
        return any(field.has_autocomplete() for field in self.fields)

    def get_dependent_fields(self) -> List[ServiceDeskFormField]:
        """
        Get a list of all fields that have dependencies on other fields.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of fields with dependencies.
        """
        return [field for field in self.fields if field.is_dependent()]


class ServiceDeskFormParser:
    """
    Class to parse JSON responses from the Atlassian Service Desk API
    and convert them into instances of ServiceDeskForm, ServiceDeskFormField,
    and ServiceDeskFormFieldValue.

    Methods
    -------
    parse(json_data: Dict[str, Any]) -> ServiceDeskForm
        Parses the JSON data and returns a ServiceDeskForm object.
    _parse_field(field_data: Dict[str, Any]) -> List[ServiceDeskFormField]
        Parses a single field's data and returns a list of ServiceDeskFormField objects,
        including the main field and subfields.
    _parse_values(values_data: List[Dict[str, Any]], parent_field_id: str = "") -> List[ServiceDeskFormFieldValue]
        Parses a list of values and returns a list of ServiceDeskFormFieldValue objects.
    _parse_proforma_fields(proforma_data: Dict[str, Any]) -> List[ServiceDeskFormField]
        Parses proforma fields and returns a list of ServiceDeskFormField objects.
    _parse_cascadingselect_field(field: ServiceDeskFormField) -> List[ServiceDeskFormField]
        Parses and adds subfields for a cascadingselect field.
    """

    @staticmethod
    def parse(json_data: Dict[str, Any]) -> ServiceDeskForm:
        """
        Parses the JSON data and returns a ServiceDeskForm object.

        Parameters
        ----------
        json_data : Dict[str, Any]
            The JSON data from the Atlassian Service Desk API.

        Returns
        -------
        ServiceDeskForm
            An instance of ServiceDeskForm containing parsed data.
        """
        form_id = json_data["portal"]["id"]
        request_type_id = json_data["reqCreate"]["id"]
        service_desk_id = json_data["portal"]["serviceDeskId"]
        project_id = json_data["portal"]["projectId"]
        portal_name = json_data["portal"]["name"]
        portal_description = json_data["portal"].get("description", "")
        form_name = json_data["reqCreate"]["form"]["name"]
        form_description_html = json_data["reqCreate"]["form"]["descriptionHtml"]

        fields_data = json_data["reqCreate"]["fields"]
        fields = []
        for field_data in fields_data:
            if (
                "autoCompleteUrl" not in field_data.keys()
                or field_data["autoCompleteUrl"] == ""
            ):
                parsed_fields = ServiceDeskFormParser._parse_field(field_data)
                fields.extend(parsed_fields)

        if "proformaTemplateForm" in json_data["reqCreate"]:
            proforma_fields = ServiceDeskFormParser._parse_proforma_fields(
                json_data["reqCreate"]["proformaTemplateForm"]
            )
            fields.extend(proforma_fields)

        parsed_fields = ServiceDeskFormParser._parse_autocomplete_fields(json_data)
        fields.extend(parsed_fields)

        proforma_template_form = json_data["reqCreate"].get("proformaTemplateForm", {})
        updated_at = proforma_template_form.get("updated")

        design_settings = proforma_template_form.get("design", {}).get("settings", {})
        template_id = design_settings.get("templateId")
        template_form_uuid = design_settings.get("templateFormUuid")

        return ServiceDeskForm(
            id=form_id,
            project_id=project_id,
            request_type_id=request_type_id,
            service_desk_id=service_desk_id,
            portal_name=portal_name,
            portal_description=portal_description,
            form_name=form_name,
            form_description_html=form_description_html,
            fields=fields,
            updated_at=updated_at,
            template_id=template_id,
            template_form_uuid=template_form_uuid,
            atl_token=json_data.get("xsrfToken", None),
        )

    @staticmethod
    def _parse_field(field_data: Dict[str, Any]) -> List[ServiceDeskFormField]:
        """
        Parses a single field's data and returns a list of ServiceDeskFormField objects,
        including the main field and any subfields if they exist.

        Parameters
        ----------
        field_data : Dict[str, Any]
            The JSON data for a single field.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of ServiceDeskFormField objects, including the main field and subfields.
        """
        field_type = field_data["fieldType"]
        field_id = field_data["fieldId"]
        field_config_id = field_data.get("fieldConfigId", "")
        label = field_data["label"]
        description = field_data.get("description", "")
        description_html = field_data.get("descriptionHtml", "")
        required = field_data["required"]
        displayed = field_data["displayed"]
        preset_values = field_data.get("presetValues", [])

        values_data = field_data.get("values", [])
        values = ServiceDeskFormParser._parse_values(values_data, field_id)

        renderer_type = field_data.get("rendererType")
        auto_complete_url = field_data.get("autoCompleteUrl")
        depends_on = field_data.get("depends_on")

        main_field = ServiceDeskFormField(
            field_type=field_type,
            field_id=field_id,
            field_config_id=field_config_id,
            label=label,
            description=description,
            description_html=description_html,
            required=required,
            displayed=displayed,
            preset_values=preset_values,
            values=values,
            renderer_type=renderer_type,
            auto_complete_url=auto_complete_url,
            depends_on=depends_on,
            children=[],
        )

        if field_type == "cascadingselect":
            return ServiceDeskFormParser._parse_cascadingselect_field(main_field)
        else:
            return [main_field]

    @staticmethod
    def _parse_autocomplete_values(values_data: Any) -> List[ServiceDeskFormFieldValue]:
        """
        Transforms a single result entry from the original JSON format to the new format.

        Parameters
        ----------
        values_data : Dict[str, Any]
            A single result entry from the original JSON.

        Returns
        -------
        Dict[str, Any]
            The transformed values_data entry.
        """
        values = []
        for value_data in values_data["results"]:
            object_type = value_data["objectType"]
            attributes = value_data["attributes"][0]
            value_dict = {
                "value": value_data["objectId"],
                "label": value_data["label"],
                "additional_data": {
                    "workspaceId": value_data["workspaceId"],
                    "objectKey": value_data["objectKey"],
                    "objectType": {
                        "objectTypeId": object_type["objectTypeId"],
                        "id": object_type["id"],
                        "name": object_type["name"],
                        "description": object_type["description"],
                    },
                    "objectTypeAttributeId": attributes["objectTypeAttributeId"],
                    "objectTypeAttributeName": attributes["objectTypeAttribute"][
                        "name"
                    ],
                    "objectTypeAttributeType": attributes["objectTypeAttribute"][
                        "type"
                    ],
                    "objectTypeAttributeDescription": attributes["objectTypeAttribute"][
                        "description"
                    ],
                    "objectTypeAttributeValues": attributes["objectAttributeValues"],
                },
                "selected": False,
                "children": [],
            }
            field_value = ServiceDeskFormFieldValue(**value_dict)
            values.append(field_value)
        return values

    @staticmethod
    def _parse_autocomplete_fields(
        values_data: Dict[str, Any]
    ) -> List[ServiceDeskFormField]:
        """
        Parses Proforma fields and returns a list of ServiceDeskFormField objects.

        Parameters
        ----------
        proforma_data : Dict[str, Any]
            The JSON data containing Proforma fields.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of ServiceDeskFormField objects parsed from Proforma fields.
        """
        autocomplete_fields = []
        fields = values_data["reqCreate"]["fields"]
        for field in fields:
            if (
                "autoCompleteUrl" in field.keys()
                and field["autoCompleteUrl"] != ""
                and field["fieldType"] == "cmdbobjectpicker"
            ):
                is_proforma_field = False
                proforma_question_id = None
                autocomplete_values = [
                    field_data
                    for field_data in values_data["reqCreate"]["autocompleteOptions"]
                    if field_data["fieldId"] == field["fieldId"]
                ][0]
                values = ServiceDeskFormParser._parse_autocomplete_values(
                    autocomplete_values,
                )
                field_field = ServiceDeskFormField(
                    field_type=field.get("fieldType", ""),
                    field_id=field.get("fieldId", ""),
                    field_config_id="",
                    label=field.get("label"),
                    description=field.get("description", ""),
                    description_html="",
                    required=field.get("required", False),
                    displayed=field.get("displayed", False),
                    preset_values=field.get("presetValues", []),
                    values=[value for value in values if value],
                    is_proforma_field=is_proforma_field,
                    proforma_question_id=proforma_question_id,
                )
                autocomplete_fields.append(field_field)
        return autocomplete_fields

    @staticmethod
    def _parse_proforma_values(
        values_data: List[Dict[str, Any]]
    ) -> List[ServiceDeskFormFieldValue]:
        """
        Parses a list of values and returns a list of ServiceDeskFormFieldValue objects.

        Parameters
        ----------
        values_data : List[Dict[str, Any]]
            The JSON data for a list of values.
        parent_field_id : str, optional
            The ID of the parent field, used to generate subfield IDs.

        Returns
        -------
        List[ServiceDeskFormFieldValue]
            A list of ServiceDeskFormFieldValue objects.
        """
        values = []
        for value_data in values_data:
            value = value_data["id"]
            label = value_data["label"]

            field_value = ServiceDeskFormFieldValue(
                value=value, label=label, selected=None, children=None
            )
            values.append(field_value)
        return values

    @staticmethod
    def _parse_values(
        values_data: List[Dict[str, Any]], parent_field_id: str = ""
    ) -> List[ServiceDeskFormFieldValue]:
        """
        Parses a list of values and returns a list of ServiceDeskFormFieldValue objects.

        Parameters
        ----------
        values_data : List[Dict[str, Any]]
            The JSON data for a list of values.
        parent_field_id : str, optional
            The ID of the parent field, used to generate subfield IDs.

        Returns
        -------
        List[ServiceDeskFormFieldValue]
            A list of ServiceDeskFormFieldValue objects.
        """
        values = []
        for index, value_data in enumerate(values_data):
            value = value_data["value"]
            label = value_data["label"]
            selected = value_data.get("selected", False)

            children_data = value_data.get("children", [])
            children = (
                ServiceDeskFormParser._parse_values(
                    children_data, f"{parent_field_id}:{index+1}"
                )
                if children_data
                else []
            )

            field_value = ServiceDeskFormFieldValue(
                value=value, label=label, selected=selected, children=children
            )
            values.append(field_value)
        return values

    @staticmethod
    def _parse_proforma_fields(
        proforma_data: Dict[str, Any]
    ) -> List[ServiceDeskFormField]:
        """
        Parses Proforma fields and returns a list of ServiceDeskFormField objects.

        Parameters
        ----------
        proforma_data : Dict[str, Any]
            The JSON data containing Proforma fields.

        Returns
        -------
        List[ServiceDeskFormField]
            A list of ServiceDeskFormField objects parsed from Proforma fields.
        """
        fields = []
        questions = proforma_data.get("design", {}).get("questions", {})
        for question_id, question_data in questions.items():
            field_type = question_data["type"]
            field_id = question_data.get("jiraField", question_id)
            label = question_data["label"]
            description = question_data.get("description", "")
            required = question_data.get("validation", {}).get("rq", False)
            values = proforma_data["proformaFieldOptions"]["fields"].get(field_id, [])

            field = ServiceDeskFormField(
                field_type=field_type,
                field_id=field_id,
                field_config_id="",
                label=label,
                description=description,
                description_html="",
                required=required,
                displayed=True,
                preset_values=[],
                values=ServiceDeskFormParser._parse_proforma_values(values),
                is_proforma_field=True,
                proforma_question_id=question_id,
            )
            fields.append(field)
        return fields

    @staticmethod
    def _parse_cascadingselect_field(
        field: ServiceDeskFormField,
    ) -> List[ServiceDeskFormField]:
        """
        Parses and adds subfields for a cascadingselect field.

        Parameters
        ----------
        field : ServiceDeskFormField
            The main cascadingselect field.

        Returns
        -------
        List[ServiceDeskFormField]
            A list containing the main field and its subfield.
        """
        fields = [field]

        if field.field_type == "cascadingselect" and field.values:
            subfield_id = f"{field.field_id}:1"
            subfield_label = f"{field.label} (Subfield)"
            subfield = ServiceDeskFormField(
                field_type=field.field_type,
                field_id=subfield_id,
                field_config_id=field.field_config_id,
                label=subfield_label,
                description=field.description,
                description_html=field.description_html,
                required=field.required,
                displayed=field.displayed,
                preset_values=field.preset_values,
                values=[],
                renderer_type=field.renderer_type,
                auto_complete_url=field.auto_complete_url,
                depends_on=field.field_id,
                children=[],
            )
            fields.append(subfield)

        return fields
