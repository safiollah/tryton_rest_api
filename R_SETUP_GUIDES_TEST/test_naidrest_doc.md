# Documentation for test_naiadrest.py

This script tests the functionality of the Tryton REST API using the `naiad` client library. It performs various operations on the `party.party` model.

## Setup and Configuration

1.  **Imports:** The script imports necessary libraries like `os`, `sys`, `pprint`, `requests`, `json`, and `naiad`.
2.  **Configuration:**
    *   `TRYTON_URL`: The base URL of the Tryton server (default: `http://localhost:8080`).
    *   `DATABASE`: The name of the Tryton database (default: `trytonDB`).
    *   `API_KEY`: The API key obtained from a Tryton User Application. **This needs to be configured correctly.**

## `test_naiad_rest_api()` Function

This function orchestrates the testing process.

1.  **Client Initialization:**
    *   A `naiad.Client` instance is created, configured with the base URL, API key, usages (`default`), context (setting company ID to 1), and languages (`en`).

2.  **Resource Tracking:**
    *   An empty dictionary `created_resources` is initialized to keep track of resources created during the tests, allowing for cleanup later.

3.  **Test Sequence:**
    *   **Test 1: Search Parties:**
        *   Uses `client.search()` to find up to 5 active parties (`[["active", "=", True]]`).
        *   Prints the ID and `rec_name` of found parties.
        *   Handles potential exceptions during the search.
    *   **Test 2: Get Single Party:**
        *   If the search in Test 1 found parties, it takes the ID of the first party.
        *   Uses `client.get()` to retrieve the full details of that party.
        *   Prints the party's ID and `rec_name`.
        *   Uses `pprint(party.to_dict())` to print a dictionary representation of the party's data.
        *   Iterates through the party object's attributes to display all available fields and their values.
        *   Handles potential exceptions.
    *   **Test 3: Create Party via REST:**
        *   Constructs the direct REST API endpoint URL (`<TRYTON_URL>/<DATABASE>/rest/model/party.party`).
        *   Sets up headers, including the `Authorization` Bearer token and `Content-Type`.
        *   Defines a JSON payload to create a new party named "Test Party via REST".
        *   Uses the `requests.post()` method to send the creation request directly to the REST endpoint (bypassing the `naiad` client for this specific test).
        *   Checks the response status code. If successful (200), it parses the JSON response.
        *   If the response contains an `id`, it uses `client.get()` to retrieve the newly created party using `naiad` and stores it in `created_resources` for potential cleanup.
        *   Prints the result or error messages.
        *   Handles potential exceptions.
    *   **Test 4: Update Party:**
        *   Attempts to update the party created in Test 3.
        *   If the creation failed but parties were found in Test 1, it uses the first existing party for the update test.
        *   Creates a `naiad.Record` instance for the update, setting only the `id` and the modified `name`.
        *   Prints the update payload using `pprint(party_to_update.to_dict())`.
        *   Uses `client.store()` to send the update to Tryton.
        *   Prints the ID and new name of the updated party.
        *   Handles potential exceptions, including printing the error response text if available.
    *   **Test 5: Pagination Search:**
        *   Uses `client.search()` with the `range_=(0, 9)` argument to test range-based pagination.
        *   Retrieves the first 10 records (index 0 to 9).
        *   Prints the range information (`start`, `end`, `total`) returned by the server and the number of parties received in the current page.
        *   Handles potential exceptions.
    *   **Test 6: Delete Party:**
        *   Checks if a party was successfully created and stored in `created_resources` (from Test 3).
        *   If yes, it uses `client.delete()` to delete that party.
        *   Prints a confirmation message.
        *   If no party was created, it skips the deletion test.
        *   Handles potential exceptions.

4.  **Completion Message:** Prints "Tests completed."

## Execution (`if __name__ == "__main__":`)

*   The script calls the `test_naiad_rest_api()` function when run directly.

## How to Run

1.  Ensure you have a running Tryton instance accessible at the configured `TRYTON_URL` and `DATABASE`.
2.  Create a User Application in Tryton and obtain its API key.
3.  Replace the placeholder `API_KEY` in the script with your actual key.
4.  Install necessary libraries (`pip install naiad requests`).
5.  Run the script from your terminal: `python CustomTest/test_naiadrest.py` 