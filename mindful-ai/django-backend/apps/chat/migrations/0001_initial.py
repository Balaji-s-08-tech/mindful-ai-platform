
import uuid
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, help_text='Unique identifier for this record (UUID v4).', primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Timestamp when this record was created (UTC).')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp when this record was last updated (UTC).')),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Soft-delete flag. When True the record is treated as deleted.')),
                ('title', models.CharField(default='New Conversation', help_text='Display title for the conversation, auto-generated from the first message.', max_length=200)),
                ('emotion_summary', models.JSONField(blank=True, default=dict, help_text='Aggregated emotion data for this session. Schema: {"dominant": str | null, "progression": [str, ...]}')),
                ('message_count', models.PositiveIntegerField(default=0, help_text='Denormalised count of user + assistant messages in this session.')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Whether this session is currently active.')),
            ],
            options={
                'verbose_name': 'Chat Session',
                'verbose_name_plural': 'Chat Sessions',
                'db_table': 'chat_sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for this message (UUID v4).', primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')], help_text='Sender role: user, assistant, or system.', max_length=20)),
                ('content', models.TextField(help_text='Text body of the message (max 10 000 characters).', max_length=10000)),
                ('emotion_context', models.JSONField(blank=True, default=dict, help_text='Emotion snapshot at the time this message was sent. Keys: facial, voice, text, combined.')),
                ('tokens', models.PositiveIntegerField(blank=True, help_text='Token count consumed by the LLM to produce this message (AI messages only).', null=True)),
                ('model', models.CharField(blank=True, default='', help_text='LLM model identifier used to generate this message (AI messages only).', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Timestamp when this message was created (UTC).')),
            ],
            options={
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
                'db_table': 'chat_messages',
                'ordering': ['created_at'],
            },
        ),
    ]
