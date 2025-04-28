import json
import logging
from trytond.wsgi import app, Response
from trytond.protocols.wrappers import HTTPStatus
from trytond.pool import Pool
from trytond.exceptions import LoginException, RateLimitException
from trytond import backend
from trytond.protocols.wrappers import (
    allow_null_origin,
    with_pool,
    with_transaction,
    exceptions,
)

# Configure logger
logger = logging.getLogger(__name__)

def validate_login_data(data):
    """Validate login request data"""
    if not data:
        return False, "Missing request body"
    if not isinstance(data, dict):
        return False, "Invalid request format"
    if 'username' not in data or not data['username']:
        return False, "Username is required"
    if 'password' not in data or not data['password']:
        return False, "Password is required"
    return True, None


@app.route('/<database_name>/rest-login', methods=['POST'])
@with_pool 
@with_transaction()
def rest_login(request, pool):
    """
    Custom REST endpoint for login.
    
    Accepts JSON body with username and password credentials.
    Validates against Tryton's user database and returns a REST API key.
    
    Returns:
        Response: JSON response with API key or error message
    """            
    User = pool.get('res.user')
    UserApplication = pool.get('res.user.application')

    try:
        # 1. Get and validate credentials from request body
        data = request.get_json()
        is_valid, error_msg = validate_login_data(data)
        if not is_valid:
            return Response(
                json.dumps({'error': error_msg}),
                status=HTTPStatus.BAD_REQUEST,
                content_type='application/json'
            )
        
        username = data['username']
        password = data['password']
        
        login_parameters = {'password': password}

        logger.info("REST login attempt received")

        # 2. Validate credentials using Tryton's internal logic
        user_id = User.get_login(username, login_parameters)
        
        # Check if get_login returned None (indicating invalid credentials)
        if user_id is None:
            raise LoginException(username, "Invalid credentials")

        logger.info("Credentials validated successfully")
            

        # 3. Fetch the 'rest' API Key for the validated user
        application_keys = UserApplication.search_read(
            domain=[
                ('user', '=', user_id),
                ('application', '=', 'rest'),
            ],
            fields_names=['key'],
            limit=1
        )

        if not application_keys:
            logger.warning(f"API key 'rest' not found for authenticated user")
            return Response(
                json.dumps({'error': "API key not configured for this user"}),
                status=HTTPStatus.NOT_FOUND,
                content_type='application/json'
            )

        api_key = application_keys[0].get('key')

        if not api_key:
            logger.error("Found application record but key field is empty")
            return Response(
                json.dumps({'error': "Authentication system misconfiguration"}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )

        logger.info("REST API key retrieved successfully")
        
        # 4. Return the API Key
        return Response(
            json.dumps({'api_key': api_key}),
            status=HTTPStatus.OK,
            content_type='application/json'
        )

    except LoginException:
        logger.warning("Invalid credentials provided")
        return Response(
            json.dumps({'error': 'Invalid credentials'}),
            status=HTTPStatus.UNAUTHORIZED,
            content_type='application/json'
        )
    except RateLimitException:
        logger.warning("Authentication rate limit exceeded")
        return Response(
            json.dumps({'error': 'Rate limit exceeded'}),
            status=HTTPStatus.TOO_MANY_REQUESTS,
            content_type='application/json'
        )
    except backend.DatabaseOperationalError as e:
        logger.error(f"Database error during authentication: {str(e)}")
        return Response(
            json.dumps({'error': 'Database connection error'}),
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type='application/json'
        )
    except Exception as e:
        # Log the full error internally but don't expose details to client
        logger.error(f"Unexpected error during REST login: {str(e)}", exc_info=True)
        return Response(
            json.dumps({'error': 'An unexpected server error occurred'}),
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type='application/json'
        )
