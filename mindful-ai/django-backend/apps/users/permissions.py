
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

class IsNotAuthenticated(BasePermission):
    
    message = 'You are already authenticated.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        
        return not request.user.is_authenticated
