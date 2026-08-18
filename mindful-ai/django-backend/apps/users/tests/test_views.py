
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apps.users import services

User = get_user_model()

def auth_headers(user):
    
    refresh = RefreshToken.for_user(user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}

class RegisterViewTest(APITestCase):
    
    url = '/api/auth/register'

    def test_register_success(self) -> None:
        
        response = self.client.post(self.url, {
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'StrongPass1!',
            'password_confirm': 'StrongPass1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])

    def test_register_duplicate_email(self) -> None:
        
        services.create_user('Existing', 'dup@example.com', 'ExistPass1!')
        response = self.client.post(self.url, {
            'name': 'Another',
            'email': 'dup@example.com',
            'password': 'AnotherPass1!',
            'password_confirm': 'AnotherPass1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(response.data['success'])

    def test_register_password_mismatch(self) -> None:
        
        response = self.client.post(self.url, {
            'name': 'User',
            'email': 'mismatch@example.com',
            'password': 'Pass123!',
            'password_confirm': 'Different1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self) -> None:
        
        response = self.client.post(self.url, {
            'name': 'User',
            'email': 'not-an-email',
            'password': 'Pass123!',
            'password_confirm': 'Pass123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self) -> None:
        
        response = self.client.post(self.url, {'email': 'a@b.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class LoginViewTest(APITestCase):
    
    url = '/api/auth/login'

    def setUp(self) -> None:
        self.user = services.create_user('Login', 'login@example.com', 'LoginPass1!')

    def test_login_success(self) -> None:
        
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'LoginPass1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertIn('user', response.data['data'])

    def test_login_wrong_password(self) -> None:
        
        response = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'WrongPass1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_login_unknown_email(self) -> None:
        
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'Pass1!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class MeViewTest(APITestCase):
    
    url = '/api/auth/me'

    def setUp(self) -> None:
        self.user = services.create_user('Me', 'me@example.com', 'MePass1!')

    def test_me_authenticated(self) -> None:
        
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['email'], 'me@example.com')

    def test_me_unauthenticated(self) -> None:
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserProfileViewTest(APITestCase):
    
    url = '/api/users/profile'

    def setUp(self) -> None:
        self.user = services.create_user('Prof', 'prof@example.com', 'ProfPass1!')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}'
        )

    def test_get_profile(self) -> None:
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['email'], 'prof@example.com')

    def test_update_name(self) -> None:
        
        response = self.client.patch(self.url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['user']['name'], 'Updated Name')

class ChangePasswordViewTest(APITestCase):
    
    url = '/api/users/change-password'

    def setUp(self) -> None:
        self.user = services.create_user('Chg', 'chg@example.com', 'OldPass1!')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}'
        )

    def test_change_password_success(self) -> None:
        
        response = self.client.post(self.url, {
            'current_password': 'OldPass1!',
            'new_password': 'NewPass2@',
            'new_password_confirm': 'NewPass2@',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_current(self) -> None:
        
        response = self.client.post(self.url, {
            'current_password': 'WrongOld1!',
            'new_password': 'NewPass2@',
            'new_password_confirm': 'NewPass2@',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteAccountViewTest(APITestCase):
    
    url = '/api/users/profile'

    def setUp(self) -> None:
        self.user = services.create_user('Del', 'del2@example.com', 'DelPass1!')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}'
        )

    def test_delete_account_soft_deletes(self) -> None:
        
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
