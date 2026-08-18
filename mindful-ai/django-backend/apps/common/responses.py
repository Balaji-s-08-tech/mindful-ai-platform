
from typing import Any

from rest_framework import status
from rest_framework.response import Response

def success_response(
    data: Any = None,
    message: str = 'Success',
    status_code: int = status.HTTP_200_OK,
) -> Response:
    
    payload: dict = {
        'success': True,
        'message': message,
        'data': data if data is not None else {},
    }
    return Response(payload, status=status_code)

def error_response(
    message: str = 'An error occurred',
    errors: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    
    payload: dict = {
        'success': False,
        'message': message,
        'errors': errors if errors is not None else {},
    }
    return Response(payload, status=status_code)

def created_response(
    data: Any = None,
    message: str = 'Created successfully',
) -> Response:
    
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
    )

def no_content_response(message: str = 'Deleted successfully') -> Response:
    
    payload: dict = {
        'success': True,
        'message': message,
        'data': {},
    }
    return Response(payload, status=status.HTTP_200_OK)
