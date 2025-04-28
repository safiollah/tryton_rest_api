#################
Rest Login Module
#################

.. toctree::
   :maxdepth: 2

   setup
   usage
   configuration
   design
   reference
   releases

Rest Login Module
===============

This module provides a secure REST API for user authentication in Tryton,
enabling clients to login, logout, and validate tokens via HTTP requests.

API Endpoints
------------

1. Login
   
   ``POST /<database_name>/rest/login``
   
   Request body: ``{"login": "username", "password": "password"}``
   
   Response: ``{"token": "base64_encoded_token", "user_id": 123, "username": "username"}``

2. Logout
   
   ``POST /<database_name>/rest/logout``
   
   Headers: ``Authorization: Session base64_encoded_token``
   
   Response: ``{"success": true}``

3. Token Validation
   
   ``GET /<database_name>/rest/validate_token``
   
   Headers: ``Authorization: Session base64_encoded_token``
   
   Response: ``{"user_id": 123, "username": "username", "valid": true}``

Error Responses
--------------

- ``400 Bad Request``: Missing login or password
- ``401 Unauthorized``: Invalid credentials or invalid token
- ``429 Too Many Requests``: Rate limit exceeded
- ``500 Internal Server Error``: Server error

Usage in Client Applications
---------------------------

In client applications, store the token securely and include it in the
Authorization header for all subsequent API calls:

.. code-block:: javascript

    // Example JavaScript fetch call
    fetch('http://localhost:8000/database_name/rest/model/res.user/1', {
        method: 'GET',
        headers: {
            'Authorization': 'Session ' + token,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => console.log(data));

Example Usage
------------

Login and get token::

    curl -X POST http://localhost:8000/mydatabase/rest/login \
      -H "Content-Type: application/json" \
      -d '{"login": "admin", "password": "admin"}'

Making authenticated requests::

    curl -X GET http://localhost:8000/mydatabase/rest/model/res.user \
      -H "Authorization: Session YOUR_TOKEN_HERE"

Validating token::

    curl -X GET http://localhost:8000/mydatabase/rest/validate_token \
      -H "Authorization: Session YOUR_TOKEN_HERE"

Logout::

    curl -X POST http://localhost:8000/mydatabase/rest/logout \
      -H "Authorization: Session YOUR_TOKEN_HERE"

Configuration
------------

The module uses Tryton's standard configuration settings:

- ``session.timeout``: Token expiration time in seconds (default: 2592000 - 30 days)
- ``session.max_attempt``: Maximum failed login attempts (default: 5)

Security Considerations
---------------------

- Tokens are stored in memory and will be lost when the server restarts.
- Always use HTTPS in production environments.
- The session timeout should be adjusted based on security requirements.
