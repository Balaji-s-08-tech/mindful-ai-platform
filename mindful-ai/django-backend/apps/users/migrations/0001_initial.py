
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier (UUID v4).', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Display name of the user.', max_length=100)),
                ('email', models.EmailField(db_index=True, help_text='Email address used as the login identifier.', max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user account should be considered active.')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into the Django admin.')),
                ('is_deleted', models.BooleanField(db_index=True, default=False, help_text='Soft-delete flag. When True the account is treated as deleted.')),
                ('preferences', models.JSONField(blank=True, default=dict, help_text='User preference overrides stored as JSON. Keys: voiceEnabled, cameraEnabled, ttsProvider.')),
                ('last_active_at', models.DateTimeField(blank=True, help_text="Timestamp of the user's last activity (UTC).", null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp when the account was created (UTC).')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp of the last account update (UTC).')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier (UUID v4).', primary_key=True, serialize=False)),
                ('token', models.CharField(db_index=True, help_text='Cryptographically random token string.', max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the token was generated (UTC).')),
                ('expires_at', models.DateTimeField(help_text='Datetime after which the token is no longer valid (UTC).')),
                ('is_used', models.BooleanField(default=False, help_text='True once the token has been consumed to reset a password.')),
                ('user', models.ForeignKey(help_text='The user who requested this password reset.', on_delete=django.db.models.deletion.CASCADE, related_name='reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Password Reset Token',
                'verbose_name_plural': 'Password Reset Tokens',
                'db_table': 'password_reset_tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_4b85f2_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active', 'is_deleted'], name='users_is_acti_80025f_idx'),
        ),
    ]
