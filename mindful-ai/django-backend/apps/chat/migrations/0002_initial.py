
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='user',
            field=models.ForeignKey(help_text='The user who owns this conversation session.', on_delete=django.db.models.deletion.CASCADE, related_name='chat_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='session',
            field=models.ForeignKey(help_text='The parent conversation session.', on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.chatsession'),
        ),
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['user', '-created_at'], name='chat_session_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['user', 'is_active'], name='chat_session_user_active_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['session', 'created_at'], name='chat_msg_session_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['session', 'role'], name='chat_msg_session_role_idx'),
        ),
    ]
