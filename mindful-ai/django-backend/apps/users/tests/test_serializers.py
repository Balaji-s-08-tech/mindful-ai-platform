
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
)
from apps.users import services

User = get_user_model()

class RegisterSerializerTest(TestCase):
    
    valid_data = {
        'name': 'Test User',
        'email': 'reg@example.com',
        'password': 'RegPass1!',
        'password_confirm': 'RegPass1!',
    }

    def test_valid_data(self) -> None:
        
        s = RegisterSerializer(data=self.valid_data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_password_mismatch(self) -> None:
        
        data = {**self.valid_data, 'password_confirm': 'Different1!'}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('non_field_errors', s.errors)

    def test_invalid_email(self) -> None:
        
        data = {**self.valid_data, 'email': 'not-an-email'}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_short_password(self) -> None:
        
        data = {**self.valid_data, 'password': 'Ab1!', 'password_confirm': 'Ab1!'}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_missing_name(self) -> None:
        
        data = {k: v for k, v in self.valid_data.items() if k != 'name'}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

class ChangePasswordSerializerTest(TestCase):
    
    def setUp(self) -> None:
        self.user = services.create_user('Chg', 'chgser@example.com', 'OldPass1!')

    def test_valid_change(self) -> None:
        
        s = ChangePasswordSerializer(
            data={
                'current_password': 'OldPass1!',
                'new_password': 'NewPass2@',
                'new_password_confirm': 'NewPass2@',
            },
            context={'request': type('R', (), {'user': self.user})()},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_new_password_mismatch(self) -> None:
        
        s = ChangePasswordSerializer(
            data={
                'current_password': 'OldPass1!',
                'new_password': 'NewPass2@',
                'new_password_confirm': 'DifferentNew2@',
            },
            context={'request': type('R', (), {'user': self.user})()},
        )
        self.assertFalse(s.is_valid())

class ResetPasswordSerializerTest(TestCase):
    
    def test_valid_reset(self) -> None:
        
        s = ResetPasswordSerializer(data={
            'token': 'some-valid-token',
            'new_password': 'ResetPass1!',
            'new_password_confirm': 'ResetPass1!',
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_password_mismatch(self) -> None:
        
        s = ResetPasswordSerializer(data={
            'token': 'tok',
            'new_password': 'ResetPass1!',
            'new_password_confirm': 'Different1!',
        })
        self.assertFalse(s.is_valid())

    def test_missing_token(self) -> None:
        
        s = ResetPasswordSerializer(data={
            'new_password': 'ResetPass1!',
            'new_password_confirm': 'ResetPass1!',
        })
        self.assertFalse(s.is_valid())
        self.assertIn('token', s.errors)
