
from typing import Any

from rest_framework.response import Response

from apps.common.responses import error_response, success_response

class StandardResponseMixin:
    
    def success(
        self,
        data: Any = None,
        message: str = 'Success',
        status_code: int = 200,
    ) -> Response:
        
        return success_response(data=data, message=message, status_code=status_code)

    def error(
        self,
        message: str = 'An error occurred',
        errors: Any = None,
        status_code: int = 400,
    ) -> Response:
        
        return error_response(message=message, errors=errors, status_code=status_code)
