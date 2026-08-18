
import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.users.models import PasswordResetToken

User = get_user_model()

class UserModelTest(TestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email='Test@Example.com',
            password='TestPass1!',
            name='Test User',
        )

    def test_user_created(self) -> None:
        
        self.assertIsNotNone(self.user.pk)
        self.assertEqual(self.user.name, 'Test User')

    def test_email_is_lowercase(self) -> None:
        
        self.assertEqual(self.user.email, 'test@example.com')

    def test_password_is_hashed(self) -> None:
        
        self.assertNotEqual(self.user.password, 'TestPass1!')
        self.assertTrue(self.user.check_password('TestPass1!'))

    def test_user_uuid_primary_key(self) -> None:
        
        self.assertIsInstance(self.user.id, uuid.UUID)

    def test_user_str(self) -> None:
        
        s = str(self.user)
        self.assertIn('Test User', s)
        self.assertIn('test@example.com', s)

    def test_default_preferences(self) -> None:
        
        prefs = self.user.default_preferences
        self.assertIn('voiceEnabled', prefs)
        self.assertIn('cameraEnabled', prefs)
        self.assertIn('ttsProvider', prefs)
        self.assertTrue(prefs['voiceEnabled'])
        self.assertFalse(prefs['cameraEnabled'])

    def test_preferences_override(self) -> None:
        
        self.user.preferences = {'voiceEnabled': False}
        prefs = self.user.default_preferences
        self.assertFalse(prefs['voiceEnabled'])

        self.assertFalse(prefs['cameraEnabled'])

    def test_soft_delete(self) -> None:
        
        self.user.soft_delete()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)

        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_is_active_default(self) -> None:
        
        self.assertTrue(self.user.is_active)

    def test_is_staff_default(self) -> None:
        
        self.assertFalse(self.user.is_staff)

    def test_create_superuser(self) -> None:
        
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass1!',
            name='Admin',
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_get_full_name(self) -> None:
        
        self.assertEqual(self.user.get_full_name(), 'Test User')

class PasswordResetTokenModelTest(TestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email='reset@example.com',
            password='TestPass1!',
            name='Reset User',
        )

    def _make_token(self, offset_hours: int = 1) -> PasswordResetToken:
        
        return PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-' + str(uuid.uuid4().hex[:8]),
            expires_at=timezone.now() + timedelta(hours=offset_hours),
        )

    def test_valid_token(self) -> None:
        
        token = self._make_token(1)
        self.assertTrue(token.is_valid)

    def test_expired_token(self) -> None:
        
        token = self._make_token(-1)
        self.assertFalse(token.is_valid)

    def test_used_token(self) -> None:
        
        token = self._make_token(1)
        token.is_used = True
        token.save()
        self.assertFalse(token.is_valid)

    def test_token_str(self) -> None:
        
        token = self._make_token(1)
        self.assertIn('reset@example.com', str(token))
