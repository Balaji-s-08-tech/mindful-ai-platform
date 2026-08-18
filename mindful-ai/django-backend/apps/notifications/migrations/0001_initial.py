
import uuid
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the notification.', primary_key=True, serialize=False)),
                ('title', models.CharField(help_text='Short notification title or subject line.', max_length=255)),
                ('body', models.TextField(help_text='Full body text of the notification.')),
                ('notification_type', models.CharField(choices=[('push', 'Push Notification'), ('email', 'Email'), ('in_app', 'In-App Notification'), ('sms', 'SMS')], db_index=True, default='in_app', help_text='Channel through which the notification is delivered.', max_length=20)),
                ('is_read', models.BooleanField(db_index=True, default=False, help_text='True once the user has acknowledged the notification.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='UTC timestamp when this notification was created.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='UTC timestamp when this notification was last updated.')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
    ]
