# Atlassian Forms Submitter SDK

The Atlassian Forms Submitter SDK is a Python library designed to simplify the process of interacting with Atlassian Service Desk forms. It provides a high-level interface for fetching forms, parsing their structure, managing form fields, and creating service desk requests.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Usage](#usage)
   - [Initializing the Client](#initializing-the-client)
   - [Fetching and Parsing Forms](#fetching-and-parsing-forms)
   - [Listing Fields](#listing-fields)
   - [Setting Form Values](#setting-form-values)
   - [Creating Requests](#creating-requests)
4. [Advanced Usage](#advanced-usage)
   - [Working with Cascading Select Fields](#working-with-cascading-select-fields)
   - [Handling Proforma Fields](#handling-proforma-fields)
   - [Using Autocomplete Fields](#using-autocomplete-fields)
5. [Error Handling](#error-handling)
6. [Contributing](#contributing)
7. [License](#license)

## Installation

You can install the Atlassian Forms Submitter SDK using pip:

```bash
pip install atlassian-forms-submitter-sdk
```

## Quick Start

Here's a simple example to get you started:

```python
import atlassianforms

# Initialize the client
client = atlassianforms.ServiceDeskFormClient(
    base_url="https://your-domain.atlassian.net",
    username="your-username",
    auth_token="your-api-token"
)

# Fetch and parse a form
client.fetch_and_parse_form(portal_id=1, request_type_id=2)

# List fields
client.list_fields()

# Set form values
filled_values = {
    "Summary": "Test issue",
    "Description": "This is a test issue",
    "Priority": "Medium"
}
form_filled = client.set_form_values(filled_values)

# Create a request
response = client.create_request(form_filled)
print(f"Created issue: {response.key}")
```

## Usage

### Initializing the Client

To start using the SDK, you need to initialize the `ServiceDeskFormClient` with your Atlassian credentials:

```python
from atlassianforms import ServiceDeskFormClient

client = ServiceDeskFormClient(
    base_url="https://your-domain.atlassian.net",
    username="your-username",
    auth_token="your-api-token"
)
```

### Fetching and Parsing Forms

Before you can interact with a form, you need to fetch and parse it:

```python
client.fetch_and_parse_form(portal_id=1, request_type_id=2)
```

### Listing Fields

To see all available fields in the form:

```python
fields = client.list_fields()
for field in fields:
    print(f"Field: {field['label']} (ID: {field['id']}, Type: {field['type']})")
```

### Setting Form Values

To fill out the form:

```python
filled_values = {
    "Summary": "Test issue",
    "Description": "This is a test issue",
    "Priority": "Medium"
}
form_filled = client.set_form_values(filled_values)
```

### Creating Requests

To submit the form and create a request:

```python
response = client.create_request(form_filled)
print(f"Created issue: {response.key}")
```

## Advanced Usage

### Working with Cascading Select Fields

For cascading select fields, provide both the parent and child values:

```python
filled_values = {
    "Category": "Hardware",
    "Category:1": "Laptop"
}
form_filled = client.set_form_values(filled_values)
```

### Handling Proforma Fields

Proforma fields are custom fields that may require special handling:

```python
filled_values = {
    "Summary": "Custom issue",
    "CustomField": "Custom value"  # This might be a proforma field
}
form_filled = client.set_form_values(filled_values)
```

### Using Autocomplete Fields

For fields with autocomplete functionality:

```python
# List autocomplete options
options = client.list_field_values("CMDBObjectPicker")

# Set the value
filled_values = {
    "CMDBObjectPicker": "OBJ-001"  # Use the object ID from the autocomplete options
}
form_filled = client.set_form_values(filled_values)
```

## Error Handling

The SDK uses custom exceptions to handle errors. The main exception to catch is `ServiceDeskRequestError`:

```python
from atlassianforms import ServiceDeskRequestError

try:
    response = client.create_request(form_filled)
except ServiceDeskRequestError as e:
    print(f"Failed to create request: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.