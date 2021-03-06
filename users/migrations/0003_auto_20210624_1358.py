# Generated by Django 3.2.3 on 2021-06-24 04:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_customuser_usericon'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('dt', models.DateTimeField(default=django.utils.timezone.now, verbose_name='フォロした日時')),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follow_from_user', to=settings.AUTH_USER_MODEL, verbose_name='フォロー元のユーザー')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follow_to_user', to=settings.AUTH_USER_MODEL, verbose_name='フォロー対象のユーザー')),
            ],
            options={
                'db_table': 'followuser',
            },
        ),
        migrations.CreateModel(
            name='BlockUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('dt', models.DateTimeField(default=django.utils.timezone.now, verbose_name='ブロックした日時')),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='block_from_user', to=settings.AUTH_USER_MODEL, verbose_name='ブロック元のユーザー')),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='block_to_user', to=settings.AUTH_USER_MODEL, verbose_name='ブロック対象のユーザー')),
            ],
            options={
                'db_table': 'blockuser',
            },
        ),
        migrations.AddField(
            model_name='customuser',
            name='blocked',
            field=models.ManyToManyField(blank=True, related_name='_users_customuser_blocked_+', through='users.BlockUser', to=settings.AUTH_USER_MODEL, verbose_name='ブロック'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='followed',
            field=models.ManyToManyField(blank=True, related_name='_users_customuser_followed_+', through='users.FollowUser', to=settings.AUTH_USER_MODEL, verbose_name='フォロー'),
        ),
    ]
