from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def success_response(status_code=200, data=None, message="success"):
    return error_response(status_code=status_code, message=message, data=data)

def error_response(status_code, message=None, data=None):
    if status_code > 299:
        payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    else:
        payload = {}
        
    if message:
        payload['message'] = message

    if data:
        payload['data'] = data
        
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message="Bad Request"):
    return error_response(400, message)

def unauthorized_request(message="You're not allowed to do that!"):
    return error_response(401, message)

def permissioned_denied(message="You don't have the permissions to do that!"):
    return error_response(403, message)

def server_error(message="Something went wrong! Our backend team has been notified and are working to resolve it."):
    return error_response(500, message)

def not_found(message='The object was not found!'):
    return error_response(404, message)

def unapproved_account(message='Your account has not been approved. Contact your school administrator'):
    return error_response(419, message)

class BaseError(Exception):
    '''
    Base exception for all custom API errors
    '''

    def __init__(self, message=None, error_code=400, payload=None):
        super(BaseError, self).__init__(message)
        self.error_code = error_code
        self.payload = payload
        self.message = message

    def to_dict(self):
        '''
        Get a dictionary representation of this error instance
        '''
        return error_response(status_code=self.error_code, message=self.message, data=self.payload)


class DatabaseError(BaseError):
    '''
    Generic Database Error
    '''
    def __init__(self, message="Something went wrong! Our team has been informed and are working on it."):
        super(DatabaseError, self).__init__(message, 500)
        self.payload = "DATABASE ERROR"


class DatabaseIntegrityError(BaseError):
    '''
    Integrity Error
    '''
    def __init__(self, message="Something went wrong! Our team has been informed and are working on it."):
        super(DatabaseError, self).__init__(message, 411)
        self.payload = "INTEGRITY ERROR"


class AuthenticationFailedError(BaseError):
	'''
	Error raised when authenticating a user failed
	'''
	
	def __init__(self, message='Authentication Failed. Access Denied'):
		super(AuthenticationFailedError, self).__init__(message, 401)



class PermissionDeniedError(BaseError):
    '''
     Error raised when a user does not have the requisite permission
    '''
    def __init__(self, message='You do not have permission to do that!', error_code=403):
        super(PermissionDeniedError, self).__init__(message, error_code)

