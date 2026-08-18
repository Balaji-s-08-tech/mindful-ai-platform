
import uuid
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserAnalytics',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_sessions', models.PositiveIntegerField(default=0)),
                ('total_messages', models.PositiveIntegerField(default=0)),
                ('most_common_emotion', models.CharField(blank=True, default='', max_length=50)),
                ('last_session_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'User Analytics',
                'verbose_name_plural': 'User Analytics',
                'db_table': 'user_analytics',
            },
        ),
    ]
