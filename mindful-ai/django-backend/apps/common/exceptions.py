
import logging
from typing import Any, Optional

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    
    def __init__(
        self,
        message: str = 'An application error occurred',
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def custom_exception_handler(exc: Exception, context: Any) -> Optional[Response]:
    
    if isinstance(exc, Http404):
        exc = NotFound(detail='Resource not found.')
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied(detail='Permission denied.')

    if isinstance(exc, ApplicationError):
        logger.warning('ApplicationError [%s]: %s', exc.status_code, exc.message)
        return Response(
            {
                'success': False,
                'message': exc.message,
                'errors': {},
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)

    if response is not None:
        errors: Any = response.data
        message: str = _extract_message(exc, errors)

        response.data = {
            'success': False,
            'message': message,
            'errors': errors if isinstance(errors, dict) else {'detail': errors},
        }
        return response

    logger.exception('Unhandled exception in view [%s]: %s', type(exc).__name__, exc)
    return Response(
        {
            'success': False,
            'message': 'Internal server error. Please try again later.',
            'errors': {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

def _extract_message(exc: Exception, errors: Any) -> str:
    
    if isinstance(exc, ValidationError):
        return 'Validation error. Please check the submitted data.'
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return 'Authentication required. Please log in and try again.'
    if isinstance(exc, PermissionDenied):
        return 'You do not have permission to perform this action.'
    if isinstance(exc, NotFound):
        return 'The requested resource was not found.'
    if isinstance(exc, MethodNotAllowed):
        return 'HTTP method not allowed for this endpoint.'
    if isinstance(exc, Throttled):
        return 'Too many requests. Please slow down and try again later.'
    if isinstance(errors, dict) and 'detail' in errors:
        return str(errors['detail'])
    return 'An error occurred.'
