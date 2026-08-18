
from django.urls import path

from apps.users.views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshTokenView,
    RegisterView,
    ResetPasswordView,
)

app_name = 'auth'

urlpatterns = [

    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),

    path('refresh', RefreshTokenView.as_view(), name='token-refresh'),
    path('logout', LogoutView.as_view(), name='logout'),

    path('me', MeView.as_view(), name='me'),

    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]
