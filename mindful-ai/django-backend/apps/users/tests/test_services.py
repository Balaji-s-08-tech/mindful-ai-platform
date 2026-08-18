
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.common.exceptions import ApplicationError
from apps.users import services

User = get_user_model()

class CreateUserServiceTest(TestCase):
    
    def test_create_user_success(self) -> None:
        
        user = services.create_user(
            name='New User',
            email='new@example.com',
            password='NewPass1!',
        )
        self.assertEqual(user.name, 'New User')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('NewPass1!'))

    def test_create_user_email_lowercased(self) -> None:
        
        user = services.create_user('X', 'Upper@Case.COM', 'Pass123!')
        self.assertEqual(user.email, 'upper@case.com')

    def test_create_user_duplicate_email_raises(self) -> None:
        
        services.create_user('First', 'dup@example.com', 'Pass123!')
        with self.assertRaises(ApplicationError) as ctx:
            services.create_user('Second', 'dup@example.com', 'Pass456!')
        self.assertEqual(ctx.exception.status_code, 409)

    def test_create_user_weak_password_raises(self) -> None:
        
        with self.assertRaises(ApplicationError):
            services.create_user('User', 'weak@example.com', '12345678')

class AuthenticateUserServiceTest(TestCase):
    
    def setUp(self) -> None:
        self.user = services.create_user('Auth', 'auth@example.com', 'AuthPass1!')

    def test_authenticate_correct(self) -> None:
        
        user = services.authenticate_user('auth@example.com', 'AuthPass1!')
        self.assertEqual(user, self.user)

    def test_authenticate_wrong_password(self) -> None:
        
        with self.assertRaises(ApplicationError) as ctx:
            services.authenticate_user('auth@example.com', 'WrongPass1!')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_authenticate_unknown_email(self) -> None:
        
        with self.assertRaises(ApplicationError):
            services.authenticate_user('noone@example.com', 'Pass123!')

    def test_authenticate_updates_last_active(self) -> None:
        
        services.authenticate_user('auth@example.com', 'AuthPass1!')
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_active_at)

class ChangePasswordServiceTest(TestCase):
    
    def setUp(self) -> None:
        self.user = services.create_user('Chang', 'chang@example.com', 'OldPass1!')

    def test_change_password_success(self) -> None:
        
        services.change_password(self.user, 'OldPass1!', 'NewPass2@')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass2@'))

    def test_change_password_wrong_current(self) -> None:
        
        with self.assertRaises(ApplicationError) as ctx:
            services.change_password(self.user, 'WrongOld1!', 'NewPass2@')
        self.assertEqual(ctx.exception.status_code, 400)

class UpdateProfileServiceTest(TestCase):
    
    def setUp(self) -> None:
        self.user = services.create_user('Upd', 'upd@example.com', 'UpdPass1!')

    def test_update_name(self) -> None:
        
        updated = services.update_profile(self.user, {'name': 'Updated Name'})
        self.assertEqual(updated.name, 'Updated Name')

    def test_update_preferences(self) -> None:
        
        services.update_profile(self.user, {'preferences': {'voiceEnabled': False}})
        self.user.refresh_from_db()
        self.assertFalse(self.user.preferences.get('voiceEnabled'))

class DeactivateAccountServiceTest(TestCase):
    
    def setUp(self) -> None:
        self.user = services.create_user('Del', 'del@example.com', 'DelPass1!')

    def test_deactivate_soft_deletes(self) -> None:
        
        services.deactivate_account(self.user)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
