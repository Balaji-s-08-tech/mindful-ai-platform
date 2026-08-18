
from typing import Any

from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.request import Request

__all__ = [
    'IsAuthenticated',
    'IsOwner',
    'IsOwnerOrReadOnly',
]

class IsOwner(BasePermission):
    
    message: str = 'You do not have permission to access this resource.'

    def has_permission(self, request: Request, view: Any) -> bool:
        
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: Any, obj: Model) -> bool:
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False

class IsOwnerOrReadOnly(BasePermission):
    
    message: str = 'You do not have permission to modify this resource.'

    def has_permission(self, request: Request, view: Any) -> bool:
        
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: Any, obj: Model) -> bool:
        
        if request.method in SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False
