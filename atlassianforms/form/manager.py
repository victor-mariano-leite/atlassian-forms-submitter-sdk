import json
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from atlassianforms.form.parser import (
    ServiceDeskForm,
    ServiceDeskFormField,
    ServiceDeskFormFieldValue,
)
from atlassianforms.validators.field import ServiceDeskFormValidator


@dataclass
class ServiceDeskFormFilled:
    form: ServiceDeskForm
    filled_values: Dict[str, Any] = field(default_factory=dict)

    def to_request_payload(self) -> str:
        """
        Convert the filled values into a URL-encoded string suitable for making the API request.

        This method handles both regular fields and proformaFormData fields, ensuring that
        templateId and UUID are included correctly. It also combines nested fields into a
        single field with comma-separated values.

        Returns
        -------
        str
            The URL-encoded payload for the API request.
        """
        # Process all fields and combine results
        regular_fields = self._process_regular_fields()
        proforma_data = self._construct_proforma_data()

        # Add the proformaFormData as a JSON string
        regular_fields["proformaFormData"] = json.dumps(proforma_data)
        regular_fields["projectId"] = str(self.form.project_id)

        # URL-encode the entire payload
        url_encoded_payload = urllib.parse.urlencode(regular_fields)

        return url_encoded_payload

    def _process_regular_fields(self) -> Dict[str, Any]:
        """
        Process regular fields from the filled values.

        Returns
        -------
        Dict[str, Any]
            A dictionary of regular fields with their values.
        """
        regular_fields = {}
        for field in self.form.fields:
            field_id = field.field_id
            if field_id in self.filled_values and not field.is_proforma_field:
                regular_fields[field_id] = self.filled_values[field_id]
        return regular_fields

    def _construct_proforma_data(self) -> Dict[str, Any]:
        """
        Construct the proformaFormData section of the payload.

        Returns
        -------
        Dict[str, Any]
            The proformaFormData section.
        """
        proforma_answers = {}

        for field in self.form.fields:
            field_id = field.field_id
            if field_id in self.filled_values and field.is_proforma_field:
                proforma_answers[
                    field.proforma_question_id
                ] = self._process_proforma_field(field_id, field.field_type)

        return {"templateFormId": self.form.template_id, "answers": proforma_answers}

    def _process_proforma_field(self, field_id: str, field_type: str) -> Dict[str, Any]:
        """
        Process a proforma field and convert it into the appropriate format.

        Parameters
        ----------
        field_id : str
            The ID of the field being processed.
        field_type : str
            The type of the field.

        Returns
        -------
        Dict[str, Any]
            The processed proforma field in the correct format.
        """
        # Logic made for Proforma Form fields that have options
        form_values = self.form.get_field_by_id(field_id).values
        if isinstance(form_values, list) and len(form_values) > 1:
            field_type = "cl"

        value = self.filled_values[field_id]

        # Handle rich text fields with ADF formatting
        if field_type in ["rt", "cd"]:
            return {"adf": self._create_adf_document(value)}

        # Handle choice fields
        elif field_type == "cl":
            # Convert value to the corresponding ID for the choice
            choice_id = self._get_choice_id(field_id, value)
            return {"text": "", "choices": [choice_id]}

        # Handle date-time fields
        elif field_type == "dt":
            date, time = value.split("T")
            return {"date": date, "time": time}

        # Handle simple text fields
        else:
            return {"text": value}

    def _get_choice_id(self, field_id: str, value: str) -> str:
        """
        Retrieve the ID corresponding to a choice value.

        Parameters
        ----------
        field_id : str
            The ID of the field.
        value : str
            The choice value to be converted to its ID.

        Returns
        -------
        str
            The ID corresponding to the choice value.
        """
        field = self.form.get_field_by_id(field_id)
        if not field:
            raise ValueError(f"Field ID '{field_id}' not found.")

        # Search through the field's values to find the matching ID
        for choice in field.values:
            if choice.label == value or choice.value == value:
                return choice.value

        raise ValueError(
            f"Value '{value}' not found in choices for field '{field_id}'."
        )

    def _create_adf_document(self, text: str) -> Dict[str, Any]:
        """
        Create an ADF (Atlassian Document Format) document.

        Parameters
        ----------
        text : str
            The text to include in the ADF document.

        Returns
        -------
        Dict[str, Any]
            A JSON object representing the ADF document.
        """
        return {
            "version": 1,
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ],
        }


class ServiceDeskFormManager:
    """
    Manages the ServiceDeskForm, providing functionality to list fields, list field values,
    validate the form, and set field values to create a ServiceDeskFormFilled instance.

    Attributes
    ----------
    form : ServiceDeskForm
        The ServiceDeskForm instance to manage.

    Methods
    -------
    list_fields() -> List[str]:
        Lists all field labels in the form.

    list_field_values(field_identifier: str, parent_value: Optional[str] = None) -> List[str]:
        Lists all possible values for a given field, identified by either label or ID.
        If the field has nested values, the user can pass a parent value to list the children of that value.

    validate(filled_values: Dict[str, Any]) -> bool:
        Validates the filled values according to the required fields in the form.

    set_field_values(filled_values: Dict[str, Any]) -> ServiceDeskFormFilled:
        Sets the provided values for the form fields, including compound fields with children,
        and returns a ServiceDeskFormFilled instance.
    """

    def __init__(self, form: ServiceDeskForm):
        """
        Initializes the ServiceDeskFormManager with a ServiceDeskForm.

        Parameters
        ----------
        form : ServiceDeskForm
            The ServiceDeskForm instance to manage.
        """
        self.form = form
        self.validator = ServiceDeskFormValidator()

    def create_request_payload(self, filled_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the filled values into the body format required by the API request,
        handling both regular fields and proformaFormData fields.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values.

        Returns
        -------
        Dict[str, Any]
            The payload formatted for the API request.
        """
        regular_fields = {}
        proforma_answers = {}

        for field in self.form.fields:
            field_id = field.field_id

            if field_id in filled_values:
                if field.is_proforma_field:
                    # Map the proforma question ID to the appropriate answer
                    proforma_answers[field.proforma_question_id] = filled_values[
                        field_id
                    ]
                else:
                    # Regular field processing
                    regular_fields[field_id] = filled_values[field_id]

        # Construct the proformaFormData section
        proforma_data = {
            "templateFormId": self.form.template_id,
            "answers": proforma_answers,
        }

        # Complete payload combining regular fields and proformaFormData
        payload = {**regular_fields, "proformaFormData": json.dumps(proforma_data)}

        return payload

    def list_fields(self) -> List[str]:
        """
        Lists all field labels in the form.

        Returns
        -------
        List[str]
            A list of field labels.
        """
        return [
            {
                "label": field.label,
                "id": field.field_id,
                "type": field.field_type,
                "description": field.description,
            }
            for field in self.form.fields
        ]

    def list_field_values(
        self, field_identifier: str, parent_value: Optional[str] = None
    ) -> List[str]:
        """
        Lists all possible values for a given field, identified by either label or ID.
        If the field has nested values, the user can pass a parent value to list the children of that value.

        Parameters
        ----------
        field_identifier : str
            The label or ID of the field whose values to list.
        parent_value : Optional[str]
            The value of the parent to list its children, if applicable.

        Returns
        -------
        List[str]
            A list of value labels for the given field.
        """
        field = self._get_field_by_id_or_label(field_identifier)

        if not field:
            raise ValueError(f"Field with identifier '{field_identifier}' not found.")

        if parent_value is None:
            return [
                {"label": value.label, "value": value.value} for value in field.values
            ]
        else:
            parent = self._get_value_by_label(field.values, parent_value)
            if parent:
                return [
                    {"label": child.label, "value": child.value}
                    for child in parent.children
                ]
            else:
                raise ValueError(
                    f"Parent value '{parent_value}' not found in field '{field_identifier}'."
                )

    def _get_field_by_id_or_label(
        self, identifier: str
    ) -> Optional[ServiceDeskFormField]:
        """
        Retrieves a field by its ID or label.

        Parameters
        ----------
        identifier : str
            The ID or label of the field to retrieve.

        Returns
        -------
        Optional[ServiceDeskFormField]
            The ServiceDeskFormField instance if found, None otherwise.
        """
        return next(
            (
                field
                for field in self.form.fields
                if field.field_id == identifier or field.label == identifier
            ),
            None,
        )

    def _get_value_by_label_or_id(
        self, values: List[ServiceDeskFormFieldValue], identifier: str
    ) -> Optional[ServiceDeskFormFieldValue]:
        """
        Retrieves a value by its label or ID from a list of ServiceDeskFormFieldValue instances.

        Parameters
        ----------
        values : List[ServiceDeskFormFieldValue]
            The list of ServiceDeskFormFieldValue instances to search.
        identifier : str
            The label or ID of the value to retrieve.

        Returns
        -------
        Optional[ServiceDeskFormFieldValue]
            The ServiceDeskFormFieldValue instance if found, None otherwise.
        """
        return next(
            (
                value
                for value in values
                if value.label == identifier or value.value == identifier
            ),
            None,
        )

    def validate(self, filled_values: Dict[str, Any]) -> bool:
        """
        Validates the filled values according to the required fields in the form.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values to validate.

        Returns
        -------
        bool
            True if the filled values are valid, otherwise raises an exception.
        """
        required_fields = [
            field.field_id for field in self.form.fields if field.is_required()
        ]
        missing_fields = set(required_fields) - set(filled_values.keys())

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate the consistency of the filled values
        self.validator.validate(filled_values, self.form)
        return True

    def set_field_values(self, filled_values: Dict[str, Any]) -> ServiceDeskFormFilled:
        """
        Sets the provided values for the form fields, including compound fields with children,
        and returns a ServiceDeskFormFilled instance.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values, identified by either labels or IDs.

        Returns
        -------
        ServiceDeskFormFilled
            An instance of ServiceDeskFormFilled with the provided values.
        """
        # Convert labels to IDs if necessary
        filled_values = self._convert_labels_to_ids(filled_values)

        # Validate the filled values
        self.validate(filled_values)

        # Flatten compound fields with children
        flat_filled_values = self._flatten_field_values(filled_values)

        # Create the ServiceDeskFormFilled instance
        form_filled = ServiceDeskFormFilled(
            form=self.form, filled_values=flat_filled_values
        )

        return form_filled

    def _get_value_by_label(
        self, values: List[ServiceDeskFormFieldValue], label: str
    ) -> Optional[ServiceDeskFormFieldValue]:
        """
        Retrieves a value by its label from a list of ServiceDeskFormFieldValue instances.

        Parameters
        ----------
        values : List[ServiceDeskFormFieldValue]
            The list of ServiceDeskFormFieldValue instances to search.
        label : str
            The label of the value to retrieve.

        Returns
        -------
        Optional[ServiceDeskFormFieldValue]
            The ServiceDeskFormFieldValue instance if found, None otherwise.
        """
        return next((value for value in values if value.label == label), None)

    def _convert_labels_to_ids(self, filled_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts field labels to IDs and value labels to value IDs in the filled values dictionary.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values, which may contain labels instead of IDs.

        Returns
        -------
        Dict[str, Any]
            The dictionary with labels converted to IDs.
        """
        converted_values = {}
        for field_identifier, value in filled_values.items():
            field = self._get_field_by_id_or_label(field_identifier)
            if not field:
                raise ValueError(f"Field '{field_identifier}' not found in the form.")

            # Ensure correct handling of compound fields and label-to-ID conversion
            if field.field_type in [
                "cascadingselect",
                "select",
                "radiobuttons",
                "multiselect",
            ]:
                if self._is_compound_field_value(value):
                    converted_values.update(self._convert_compound_field(field, value))
                else:
                    converted_values[field.field_id] = self._convert_single_field(
                        field, value
                    )
            else:
                # For text fields and other simple types, directly assign the value
                converted_values[field.field_id] = value

        return converted_values

    def _convert_single_field(
        self, field: ServiceDeskFormField, value: Union[str, List[str]]
    ) -> Union[str, List[str]]:
        """
        Converts a single field's value(s) from a label(s) to an ID(s).

        Parameters
        ----------
        field : ServiceDeskFormField
            The field to which the value belongs.
        value : Union[str, List[str]]
            The value label(s) to convert.

        Returns
        -------
        Union[str, List[str]]
            The value ID(s) corresponding to the label(s).
        """
        if isinstance(value, list):
            # Handle multi-select fields
            return [self._convert_single_value(field, val) for val in value]
        else:
            # Handle single value
            return self._convert_single_value(field, value)

    def _convert_single_value(self, field: ServiceDeskFormField, value: str) -> str:
        """
        Converts a single value label to its corresponding ID.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field to which the value belongs.
        value : str
            The value label to convert.

        Returns
        -------
        str
            The value ID corresponding to the label.
        """
        # Check if the field has predefined values, otherwise, return the value as is
        if field.values:
            value_obj = self._get_value_by_label_or_id(field.values, value)
            if not value_obj:
                raise ValueError(
                    f"Invalid value '{value}' for field '{field.label}' or '{field.field_id}'."
                )
            return value_obj.value
        else:
            return value

    def _convert_compound_field(
        self, field: ServiceDeskFormField, value: Union[Tuple[str, str], List[str]]
    ) -> Dict[str, str]:
        """
        Converts a compound field's values from labels to IDs.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field to which the values belong.
        value : Union[Tuple[str, str], List[str]]
            The main and sub value labels to convert.

        Returns
        -------
        Dict[str, str]
            A dictionary with the main value and sub value IDs.
        """
        main_value, sub_value = value
        main_value_obj = self._get_value_by_label_or_id(field.values, main_value)
        sub_value_obj = (
            self._get_value_by_label_or_id(main_value_obj.children, sub_value)
            if main_value_obj
            else None
        )

        if not main_value_obj or not sub_value_obj:
            raise ValueError(
                f"Invalid compound value '{main_value}, {sub_value}' for field '{field.label}' or '{field.field_id}'."
            )

        return {
            field.field_id: main_value_obj.value,
            f"{field.field_id}:1": sub_value_obj.value,
        }

    def _is_compound_field_value(self, value: Any) -> bool:
        """
        Checks if the provided value is a compound field value.

        Parameters
        ----------
        value : Any
            The value to check.

        Returns
        -------
        bool
            True if the value is a tuple with two elements, indicating a compound field; False otherwise.
        """
        return isinstance(value, tuple) and len(value) == 2

    def _flatten_field_values(self, filled_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flattens compound field values with children into a format that can be easily
        processed by the Service Desk API.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values.

        Returns
        -------
        Dict[str, Any]
            The flattened dictionary of filled field values.
        """
        flat_values = {}
        for field_id, value in filled_values.items():
            if isinstance(value, (tuple, list)) and len(value) == 2:
                main_value, sub_value = value
                flat_values[field_id] = main_value
                flat_values[f"{field_id}:1"] = sub_value
            else:
                flat_values[field_id] = value

        return flat_values
