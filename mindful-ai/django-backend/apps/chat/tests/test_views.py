
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from apps.chat.models import ChatSession, Message

User = get_user_model()

def get_tokens_for_user(user):
    
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}

class SessionListCreateViewTest(APITestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email='chat@example.com', password='TestPass1!', name='Chat User'
        )
        tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

        self.session1 = ChatSession.objects.create(user=self.user, title='Session One')
        self.session2 = ChatSession.objects.create(user=self.user, title='Session Two')

    def test_list_sessions_authenticated(self) -> None:
        
        response = self.client.get('/api/chat/sessions')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        results = response.data['data']['results']
        self.assertEqual(len(results), 2)

    def test_list_sessions_unauthenticated(self) -> None:
        
        self.client.credentials()
        response = self.client.get('/api/chat/sessions')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_sessions_only_own(self) -> None:
        
        other_user = User.objects.create_user(
            email='other@example.com', password='TestPass1!', name='Other'
        )
        ChatSession.objects.create(user=other_user, title='Other Session')
        response = self.client.get('/api/chat/sessions')
        self.assertEqual(len(response.data['data']['results']), 2)

    def test_create_session(self) -> None:
        
        response = self.client.post('/api/chat/sessions', {'title': 'New Session'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['title'], 'New Session')

    def test_create_session_default_title(self) -> None:
        
        response = self.client.post('/api/chat/sessions', {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'New Conversation')

    def test_list_excludes_soft_deleted(self) -> None:
        
        self.session1.soft_delete()
        response = self.client.get('/api/chat/sessions')
        titles = [s['title'] for s in response.data['data']['results']]
        self.assertNotIn('Session One', titles)

class SessionDetailViewTest(APITestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email='detail@example.com', password='TestPass1!', name='Detail User'
        )
        tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.session = ChatSession.objects.create(user=self.user, title='My Session')

    def test_delete_session(self) -> None:
        
        response = self.client.delete(f'/api/chat/sessions/{self.session.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertTrue(self.session.is_deleted)

    def test_delete_other_user_session_forbidden(self) -> None:
        
        other = User.objects.create_user(
            email='other2@example.com', password='TestPass1!', name='Other2'
        )
        other_session = ChatSession.objects.create(user=other, title='Other')
        response = self.client.delete(f'/api/chat/sessions/{other_session.id}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class MessageListCreateViewTest(APITestCase):
    
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email='msg2@example.com', password='TestPass1!', name='Msg User'
        )
        tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.session = ChatSession.objects.create(user=self.user)
        Message.objects.create(session=self.session, role='user', content='Hello')
        Message.objects.create(session=self.session, role='assistant', content='Hi there')

    def test_list_messages(self) -> None:
        
        response = self.client.get(f'/api/chat/sessions/{self.session.id}/messages')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 2)

    @patch('apps.chat.services.generate_response')
    def test_send_message(self, mock_ai) -> None:
        
        from apps.ai.services import AIResponse
        mock_ai.return_value = AIResponse(
            content='AI response here',
            model='gemma3:4b',
            tokens=10,
            is_crisis=False,
            provider='gemma',
            latency_ms=100,
        )
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages',
            {'content': 'How are you?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user_message', response.data['data'])
        self.assertIn('ai_message', response.data['data'])

    def test_send_message_empty_content(self) -> None:
        
        response = self.client.post(
            f'/api/chat/sessions/{self.session.id}/messages',
            {'content': '   '},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
