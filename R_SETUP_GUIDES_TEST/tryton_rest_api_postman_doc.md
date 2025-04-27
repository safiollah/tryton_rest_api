# Tryton REST API Postman Collection Documentation

This document explains the Postman collection (`tryton_rest_api_postman.json`) used for testing the Tryton REST API.

## Collection Information

- **Name:** Tryton Rest API
- **Description:** Testing Tryton REST API with naiad
- **Schema:** Postman Collection v2.1.0

## Authentication

All requests use Bearer Token authentication. The API key is stored in the `{{api_key}}` Postman variable. This key should be obtained from a User Application configured in Tryton.

## Variables

The following variables are used throughout the collection. You should configure these in your Postman environment.

- `{{tryton_url}}`: The base URL of your Tryton server (e.g., `http://localhost:8080`).
- `{{database}}`: The name of the Tryton database to connect to (e.g., `trytonDB`).
- `{{api_key}}`: The API key obtained from the Tryton User Application.
- `{{party_id}}`: The ID of a party record to use for GET, PUT, and DELETE requests. You might need to update this manually after creating or searching for a party.

## Requests

The collection includes the following requests targeting the `party.party` model:

### 1. Search Parties

- **Method:** `GET`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party`
- **Description:** Searches for party records based on specified criteria.
- **Query Parameters:**
    - `d`: The domain filter, **Base64 encoded JSON**. Example: `W1siYWN0aXZlIiwiPSIsdHJ1ZV1d` decodes to `[["active","=",true]]`. This encoding follows the decision made in the Tryton development (see [discussion](https://discuss.tryton.org/t/rest-api-for-user-application/6157)).
    - `s`: The limit (size) for the number of records returned (e.g., `5`).
- **Note:** Other parameters like `p` (offset) and `o` (order, also Base64 encoded JSON) can potentially be used.

### 2. Get Single Party

- **Method:** `GET`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party/{{party_id}}`
- **Description:** Retrieves a single party record using its ID specified in the `{{party_id}}` variable.

### 3. Create Party

- **Method:** `POST`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party`
- **Headers:**
    - `Content-Type: application/json`
- **Body (raw JSON):**
  ```json
  {
    "name": "Test Party via REST",
    "active": true
  }
  ```
- **Description:** Creates a new party record with the provided data. The response should contain the details of the created party, including its new ID.

### 4. Update Party

- **Method:** `PUT`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party/{{party_id}}`
- **Headers:**
    - `Content-Type: application/json`
- **Body (raw JSON):**
  ```json
  {
    "name": "Test Party via REST (Updated)"
  }
  ```
- **Description:** Updates an existing party record (specified by `{{party_id}}`) with the provided data. Only the fields included in the body will be updated.

### 5. Pagination (0-9)

- **Method:** `GET`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party`
- **Headers:**
    - `Range: items=0-9`
- **Description:** Retrieves a specific range of party records (items 0 to 9, inclusive, for a total of 10 items). This uses the standard HTTP `Range` header for pagination, as adopted in the Tryton REST API development (see [discussion](https://discuss.tryton.org/t/rest-api-for-user-application/6157)). The server should respond with a `Content-Range` header indicating the range returned and the total number of items.

### 6. Delete Party

- **Method:** `DELETE`
- **Endpoint:** `{{tryton_url}}/{{database}}/rest/model/party.party/{{party_id}}`
- **Description:** Deletes the party record specified by the `{{party_id}}` variable. 