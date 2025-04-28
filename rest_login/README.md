# REST Login API for Tryton

This module provides a secure REST API for user authentication in Tryton.

## Features

- Secure login endpoint
- Token-based authentication
- Token validation endpoint
- Logout functionality
- Session management
- No external dependencies

## API Endpoints

### Login

**Endpoint:** `/<database_name>/rest/login`
**Method:** `POST`
**Content-Type:** `application/json`

**Request Body:**
```json
{
    "login": "username",
    "password": "password"
}
```

**Success Response (200 OK):**
```json
{
    "token": "base64_encoded_token",
    "user_id": 123,
    "username": "username"
}
```

**Error Responses:**
- `400 Bad Request`: Missing login or password
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Token Validation

**Endpoint:** `/<database_name>/rest/validate_token`
**Method:** `GET`
**Headers:** `Authorization: Session base64_encoded_token`

**Success Response (200 OK):**
```json
{
    "user_id": 123,
    "username": "username",
    "valid": true
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid token, expired token, or token mismatch

### Logout

**Endpoint:** `/<database_name>/rest/logout`
**Method:** `POST`
**Headers:** `Authorization: Session base64_encoded_token`

**Success Response (200 OK):**
```json
{
    "success": true
}
```

## Usage Example

### Login

```bash
curl -X POST http://localhost:8000/mydatabase/rest/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "admin"}'
```

### Making Authenticated Requests

```bash
curl -X GET http://localhost:8000/mydatabase/rest/model/res.user \
  -H "Authorization: Session YOUR_TOKEN_HERE"
```

### Validating Token

```bash
curl -X GET http://localhost:8000/mydatabase/rest/validate_token \
  -H "Authorization: Session YOUR_TOKEN_HERE"
```

### Logout

```bash
curl -X POST http://localhost:8000/mydatabase/rest/logout \
  -H "Authorization: Session YOUR_TOKEN_HERE"
```

## Configuration

The module uses Tryton's standard configuration settings:

- `session.timeout`: Token expiration time in seconds (default: 2592000 - 30 days)
- `session.max_attempt`: Maximum failed login attempts (default: 5)

## Security Considerations

- Tokens are stored in memory and will be lost when the server restarts.
- Always use HTTPS in production environments.
- The session timeout should be adjusted based on security requirements. 