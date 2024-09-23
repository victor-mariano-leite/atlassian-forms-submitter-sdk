import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from atlassianforms.form.parser import (
    ServiceDeskForm,
    ServiceDeskFormField,
    ServiceDeskFormFieldValue,
)


class ServiceDeskFormValidator:
    """
    Validates the field values in a ServiceDeskForm based on their types.

    Methods
    -------
    validate(filled_values: Dict[str, Any], form: ServiceDeskForm) -> None:
        Validates all filled values based on the form's field definitions.
    _validate_dt_field(field: ServiceDeskFormField, value: str) -> None:
        Validates a date-time string for a field.
    _validate_choice_field(field: ServiceDeskFormField, value: Any) -> None:
        Validates a choice field, handling both single and compound fields.
    _validate_text_field(field: ServiceDeskFormField, value: str) -> None:
        Validates a text field.
    _validate_adf_field(field: ServiceDeskFormField, value: str) -> None:
        Validates an Atlassian Document Format (ADF) field.
    _validate_dt(value: str) -> bool:
        Checks if the date-time string is valid.
    _validate_choice(value: str, choices: List[str]) -> bool:
        Checks if the value is within allowed choices.
    _validate_text(value: str, max_length: Optional[int] = None) -> bool:
        Checks if the text is valid, optionally validating length.
    _validate_adf(value: str) -> bool:
        Checks if the ADF string is valid JSON and follows the required structure.
    """

    def validate(self, filled_values: Dict[str, Any], form: ServiceDeskForm) -> None:
        """
        Validates all filled values based on the form's field definitions.

        Parameters
        ----------
        filled_values : Dict[str, Any]
            The dictionary of filled field values to validate.
        form : ServiceDeskForm
            The form object containing field definitions.

        Raises
        ------
        ValueError
            If any field value is invalid according to its type.
        """
        for field_identifier, value in filled_values.items():
            # Check if this is a derived field (e.g., customfield_10118:1)
            field = self._get_field_by_id_or_label(form, field_identifier)

            if not field:
                raise ValueError(f"Field '{field_identifier}' not found in the form.")

            if ":" in field_identifier:  # This is a subfield in a cascading select
                self._validate_cascading_subfield(
                    form, filled_values, field_identifier, value
                )
            else:
                self._validate_generic_field(field, value)

    def _validate_cascading_subfield(
        self,
        form: ServiceDeskForm,
        filled_values: Dict[str, Any],
        field_identifier: str,
        value: str,
    ) -> None:
        """
        Validates a cascadingselect subfield by checking the main field and its associated subfield value.

        Parameters
        ----------
        form : ServiceDeskForm
            The form containing the fields.
        filled_values : Dict[str, Any]
            The dictionary of filled field values to validate.
        field_identifier : str
            The identifier of the subfield (e.g., 'customfield_10118:1').
        value : str
            The value of the subfield to validate.

        Raises
        ------
        ValueError
            If the main field or subfield value is invalid.
        """
        # Extract the main field ID
        main_field_id = field_identifier.split(":")[0]
        main_field = self._get_field_by_id_or_label(form, main_field_id)

        if not main_field:
            raise ValueError(
                f"Main field '{main_field_id}' for subfield '{field_identifier}' not found in the form."
            )

        # Validate that the main field's value is set correctly
        main_field_value = filled_values.get(main_field_id)
        if not main_field_value:
            raise ValueError(
                f"Main field '{main_field.label}' with ID '{main_field_id}' is not set, but subfield '{field_identifier}' is provided."
            )

        main_value_obj = self._get_value_by_label_or_id(
            main_field.values, main_field_value
        )
        if not main_value_obj:
            raise ValueError(
                f"Invalid main field value '{main_field_value}' for field '{main_field.label}' or '{main_field.field_id}'."
            )

        # Validate the subfield value
        subfield_value_obj = self._get_value_by_label_or_id(
            main_value_obj.children, value
        )
        if not subfield_value_obj:
            available_subfields = [child.label for child in main_value_obj.children]
            raise ValueError(
                f"Invalid subfield value '{value}' for field '{main_field.label} (Subfield)' or '{field_identifier}'. "
                f"Available subfields: {available_subfields}"
            )

    def _validate_generic_field(self, field: ServiceDeskFormField, value: Any) -> None:
        """
        Validates a generic field (non-cascadingselect) based on its type.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field object to validate.
        value : Any
            The value to validate.

        Raises
        ------
        ValueError
            If the value is not valid for the field.
        """
        if field.field_type == "dt":
            if not self._validate_dt(value):
                raise ValueError(
                    f"Invalid date-time value '{value}' for field '{field.label}' or '{field.field_id}'."
                )
        elif field.field_type in ["select", "radiobuttons", "multiselect"]:
            if not self._validate_choice(value, [v.value for v in field.values]):
                raise ValueError(
                    f"Invalid choice value '{value}' for field '{field.label}' or '{field.field_id}'."
                )
        elif field.field_type in ["textarea", "text"]:
            if not self._validate_text(value):
                raise ValueError(
                    f"Invalid text value '{value}' for field '{field.label}' or '{field.field_id}'."
                )
        elif field.field_type == "adf":
            if not self._validate_adf(value):
                raise ValueError(
                    f"Invalid ADF value '{value}' for field '{field.label}' or '{field.field_id}'."
                )

    def _validate_dt_field(self, field: ServiceDeskFormField, value: str) -> None:
        """
        Validates a date-time string for a field.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field object.
        value : str
            The value to validate.

        Raises
        ------
        ValueError
            If the value is not a valid date-time string.
        """
        if not self._validate_dt(value):
            raise ValueError(
                f"Invalid date-time value '{value}' for field '{field.label}' or '{field.field_id}'."
            )

    def _validate_choice_field(self, field: ServiceDeskFormField, value: Any) -> None:
        """
        Validates that a value is a valid choice for a field.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field object.
        value : Any
            The value to validate, can be a single value or a tuple for compound fields.

        Raises
        ------
        ValueError
            If the value is not a valid choice.
        """
        if not self._validate_choice(value, [v.value for v in field.values]):
            raise ValueError(
                f"Invalid choice value '{value}' for field '{field.label}' or '{field.field_id}'."
            )

    def _validate_choice(self, value: str, choices: List[str]) -> bool:
        """
        Validates that a value is within a list of allowed choices.

        Parameters
        ----------
        value : str
            The value to validate.
        choices : List[str]
            The list of valid choices.

        Returns
        -------
        bool
            True if the value is within the allowed choices; False otherwise.
        """
        return value in choices

    def _validate_text_field(self, field: ServiceDeskFormField, value: str) -> None:
        """
        Validates a text field.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field object.
        value : str
            The value to validate.

        Raises
        ------
        ValueError
            If the value is not valid text.
        """
        if not self._validate_text(value):
            raise ValueError(
                f"Invalid text value '{value}' for field '{field.label}' or '{field.field_id}'."
            )

    def _validate_adf_field(self, field: ServiceDeskFormField, value: str) -> None:
        """
        Validates an Atlassian Document Format (ADF) field.

        Parameters
        ----------
        field : ServiceDeskFormField
            The field object.
        value : str
            The value to validate.

        Raises
        ------
        ValueError
            If the value is not a valid ADF string.
        """
        if not self._validate_adf(value):
            raise ValueError(
                f"Invalid ADF value '{value}' for field '{field.label}' or '{field.field_id}'."
            )

    def _validate_dt(self, value: str) -> bool:
        """
        Checks if the date-time string is valid.

        Parameters
        ----------
        value : str
            The date-time string to validate.

        Returns
        -------
        bool
            True if the value is a valid date-time string; False otherwise.
        """
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M")
            return True
        except ValueError:
            return False

    def _validate_choice(self, value: str, choices: List[str]) -> bool:
        """
        Checks if the value is within allowed choices.

        Parameters
        ----------
        value : str
            The value to validate.
        choices : List[str]
            The list of valid choices.

        Returns
        -------
        bool
            True if the value is within the allowed choices; False otherwise.
        """
        return value in choices

    def _validate_text(self, value: str, max_length: Optional[int] = None) -> bool:
        """
        Checks if the text is valid, optionally validating length.

        Parameters
        ----------
        value : str
            The text value to validate.
        max_length : Optional[int]
            The maximum allowed length for the text.

        Returns
        -------
        bool
            True if the text is valid; False otherwise.
        """
        if max_length is not None and len(value) > max_length:
            return False
        return isinstance(value, str)

    def _validate_adf(self, value: str) -> bool:
        """
        Checks if the ADF string is valid JSON and follows the required structure.

        Parameters
        ----------
        value : str
            The ADF JSON string to validate.

        Returns
        -------
        bool
            True if the value is a valid ADF string; False otherwise.
        """
        try:
            adf = json.loads(value)
            if adf.get("type") == "doc" and isinstance(adf.get("content"), list):
                return True
            return False
        except json.JSONDecodeError:
            return False

    def _get_field_by_id_or_label(
        self, form: ServiceDeskForm, identifier: str
    ) -> Optional[ServiceDeskFormField]:
        """
        Retrieves a field by its ID or label from the form.

        Parameters
        ----------
        form : ServiceDeskForm
            The form containing the fields.
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
                for field in form.fields
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
