
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.chat.models import ChatSession, Message

User = get_user_model()

class ChatSessionModelTest(TestCase):
    
    def setUp(self) -> None:
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass1!',
            name='Test User',
        )
        self.session = ChatSession.objects.create(
            user=self.user,
            title='Test Session',
        )

    def test_create_session(self) -> None:
        
        self.assertEqual(self.session.title, 'Test Session')
        self.assertEqual(self.session.message_count, 0)
        self.assertTrue(self.session.is_active)
        self.assertFalse(self.session.is_deleted)
        self.assertEqual(self.session.user, self.user)

    def test_session_uuid_primary_key(self) -> None:
        
        self.assertIsInstance(self.session.id, uuid.UUID)

    def test_generate_title_short(self) -> None:
        
        self.session.generate_title('Hello there')
        self.assertEqual(self.session.title, 'Hello there')

    def test_generate_title_long(self) -> None:
        
        long_msg = 'A' * 80
        self.session.generate_title(long_msg)
        self.assertEqual(len(self.session.title), 61)
        self.assertTrue(self.session.title.endswith('…'))

    def test_soft_delete_session(self) -> None:
        
        self.session.soft_delete()
        self.session.refresh_from_db()
        self.assertTrue(self.session.is_deleted)

        self.assertTrue(ChatSession.objects.filter(id=self.session.id).exists())

    def test_str_representation(self) -> None:
        
        s = str(self.session)
        self.assertIn('Test User', s)
        self.assertIn('Test Session', s)

class MessageModelTest(TestCase):
    
    def setUp(self) -> None:
        
        self.user = User.objects.create_user(
            email='msg@example.com',
            password='TestPass1!',
            name='Msg User',
        )
        self.session = ChatSession.objects.create(user=self.user)
        self.message = Message.objects.create(
            session=self.session,
            role=Message.Role.USER,
            content='Hello AI',
        )

    def test_create_user_message(self) -> None:
        
        self.assertEqual(self.message.role, 'user')
        self.assertEqual(self.message.content, 'Hello AI')
        self.assertIsInstance(self.message.id, uuid.UUID)

    def test_create_assistant_message(self) -> None:
        
        ai_msg = Message.objects.create(
            session=self.session,
            role=Message.Role.ASSISTANT,
            content='Hello human',
            tokens=42,
            model='gemma3:4b',
        )
        self.assertEqual(ai_msg.role, 'assistant')
        self.assertEqual(ai_msg.tokens, 42)

    def test_message_roles(self) -> None:
        
        for role in [Message.Role.USER, Message.Role.ASSISTANT, Message.Role.SYSTEM]:
            msg = Message.objects.create(
                session=self.session,
                role=role,
                content=f'Test {role}',
            )
            self.assertEqual(msg.role, role)

    def test_message_emotion_context_default(self) -> None:
        
        self.assertEqual(self.message.emotion_context, {})

    def test_message_str(self) -> None:
        
        s = str(self.message)
        self.assertIn('user', s)
        self.assertIn('Hello AI', s)

    def test_messages_ordered_by_created_at(self) -> None:
        
        Message.objects.create(session=self.session, role='user', content='Second')
        messages = list(Message.objects.filter(session=self.session))
        self.assertEqual(messages[0].content, 'Hello AI')
        self.assertEqual(messages[1].content, 'Second')
