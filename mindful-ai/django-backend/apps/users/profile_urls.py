
from django.urls import path

from apps.users.views import ChangePasswordView, DeleteAccountView, UserProfileView

app_name = 'users'

urlpatterns = [

    path('profile', UserProfileView.as_view(), name='profile'),

    path('change-password', ChangePasswordView.as_view(), name='change-password'),

    path('profile/delete', DeleteAccountView.as_view(), name='delete-account'),
]
