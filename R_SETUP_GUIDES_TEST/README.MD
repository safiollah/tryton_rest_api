# Tryton REST API Test Environment Setup and Usage

This document provides guidance on setting up and testing the Tryton REST API environment within this workspace.

## 1. Setup Instructions

For detailed setup instructions, including manual version downgrades or local module installations required for this specific configuration (currently version 7.4.9), please refer to the [CHANGES.md](CHANGES.md) file.

## 2. API Testing and Interaction

Tryton exposes a REST API that allows external applications and tools to interact programmatically with its models (data structures like Parties, Products, etc.). This involves sending HTTP requests to specific endpoints.

Below are two methods demonstrated in this workspace for interacting with this REST API:

### 2.1 Python Client (naiad)

`naiad` is the official Python client library provided by Tryton. It acts as a wrapper around the REST API calls, providing convenient Python functions to interact with Tryton models (searching, retrieving, creating, updating, deleting records, etc.) from within Python scripts. Please note that `naiad` is currently considered to be in a **draft state**.

- **Script:** [`test_naiadrest.py`](test_naiadrest.py)
- **Usage:** This script demonstrates using `naiad` to make calls to the REST API endpoints. Run this script directly to perform a series of example operations against your configured Tryton instance. Ensure the `TRYTON_URL`, `DATABASE`, and `API_KEY` constants within the script are correctly set.

### 2.2 Direct HTTP Requests (Postman)

You can also interact with the Tryton REST API directly by sending HTTP requests using tools like Postman or integrating them into frontend applications.

- **Collection File:** [`tryton_rest_api_postman.json`](tryton_rest_api_postman.json)
- **Documentation:** Detailed explanations of the direct HTTP requests (endpoints, methods, headers, body formats), authentication, and required variables can be found in [`tryton_rest_api_postman_doc.md`](tryton_rest_api_postman_doc.md).
- **Usage:** Import the JSON file into Postman. Configure the necessary environment variables (`{{tryton_url}}`, `{{database}}`, `{{api_key}}`, `{{party_id}}`) as described in the documentation before sending the requests directly to the Tryton REST API endpoints.

## 3. Unittesting

To run the standard Trytond REST API unittests included within the Trytond source code:

- **Script:** [`run_tryton_tests.py`](run_tryton_tests.py)
- **Usage:** Execute this script. It dynamically loads and runs the tests from the `test_rest.py` file located within your Trytond installation (`trytond.tests.test_rest`). Ensure the `TEST_FILE_PATH` variable in the script points to the correct location of `test_rest.py` in your environment.
