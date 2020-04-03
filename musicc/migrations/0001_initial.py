# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
# Generated by Django 2.2 on 2019-08-02 09:25

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('catalog_blob', models.BinaryField()),
                ('estimated_size', models.PositiveIntegerField()),
                ('file_hash', models.CharField(max_length=500)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CatalogMapping',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('filename', models.CharField(max_length=500)),
                ('directory', models.CharField(max_length=500)),
                ('catalog_type', models.CharField(max_length=500)),
                ('catalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.Catalog')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('filename', models.CharField(blank=True, max_length=500, null=True)),
                ('file_hash', models.CharField(blank=True, max_length=500, null=True)),
                ('change_type', models.CharField(choices=[('DELETE', 'DELETE'), ('CREATE', 'CREATE')], max_length=16)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MusiccRevision',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('revision', models.CharField(max_length=31, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('revision_xsd', models.BinaryField()),
                ('file_hash', models.CharField(max_length=500)),
            ],
            options={
                'ordering': ['-updated_date_time'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MusiccScenario',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('version', models.IntegerField(blank=True, null=True)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField()),
                ('musicc_blob', models.BinaryField()),
                ('scenario_standard', models.CharField(max_length=10)),
                ('label', models.CharField(max_length=255)),
                ('file_hash', models.CharField(max_length=500)),
                ('estimated_size', models.PositiveIntegerField()),
                ('friendly_id', models.IntegerField()),
                ('instance_prefix', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='MusiccScenarioIdPool',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenDriveIdPool',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenScenarioIdPool',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=256)),
                ('musicc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScenarioImage',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('file_type', models.CharField(max_length=25)),
                ('estimated_size', models.PositiveIntegerField()),
                ('image', models.ImageField(upload_to='')),
                ('file_hash', models.CharField(max_length=500)),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='QueryCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('query_string', models.TextField()),
                ('musicc_revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccRevision')),
                ('results', models.ManyToManyField(to='musicc.MusiccScenario')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, max_length=500, unique=True)),
                ('user', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OpenScenarioRevision',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('revision', models.CharField(max_length=31, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('revision_xsd', models.BinaryField()),
                ('file_hash', models.CharField(max_length=500)),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'ordering': ['-updated_date_time'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenScenario',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField()),
                ('open_scenario_blob', models.BinaryField()),
                ('version', models.CharField(max_length=10)),
                ('file_hash', models.CharField(max_length=500)),
                ('estimated_size', models.PositiveIntegerField()),
                ('friendly_id', models.IntegerField()),
                ('instance_prefix', models.CharField(max_length=255)),
                ('catalog', models.ManyToManyField(through='musicc.CatalogMapping', to='musicc.Catalog')),
                ('revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenarioRevision', to_field='revision')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenDriveRevision',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('revision', models.CharField(max_length=31, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('revision_xsd', models.BinaryField()),
                ('file_hash', models.CharField(max_length=500)),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'ordering': ['-updated_date_time'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenDrive',
            fields=[
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField()),
                ('open_drive_blob', models.BinaryField()),
                ('sim_3d_type', models.CharField(max_length=50)),
                ('sim_id', models.IntegerField()),
                ('version', models.CharField(max_length=10)),
                ('file_hash', models.CharField(max_length=500)),
                ('estimated_size', models.PositiveIntegerField()),
                ('friendly_id', models.IntegerField()),
                ('instance_prefix', models.CharField(max_length=255)),
                ('revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenDriveRevision', to_field='revision')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NotificationExclusions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('category', models.CharField(choices=[('revision_activation', 'Revision Activation'), ('scenario_added', 'New Scenario Added'), ('comment_on_favourite', 'Comment on Favourited Scenario'), ('favourite_broken', 'Favourited Scenario Reported as Broken'), ('submission_approved', 'Submission Approved'), ('submission_denied', 'Submission Denied'), ('favourite_updated', 'Favourited Scenario Updated'), ('favourite_deleted', 'Favourited Scenario Deleted'), ('new_approval_request', 'A new approval request has been submitted'), ('software_version_upgrade', 'A new version of the MUSICC system has been deployed'), ('custom', 'A custom notification')], max_length=64)),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('message', models.CharField(max_length=256)),
                ('seen', models.BooleanField(default=False)),
                ('category', models.CharField(choices=[('revision_activation', 'Revision Activation'), ('scenario_added', 'New Scenario Added'), ('comment_on_favourite', 'Comment on Favourited Scenario'), ('favourite_broken', 'Favourited Scenario Reported as Broken'), ('submission_approved', 'Submission Approved'), ('submission_denied', 'Submission Denied'), ('favourite_updated', 'Favourited Scenario Updated'), ('favourite_deleted', 'Favourited Scenario Deleted'), ('new_approval_request', 'A new approval request has been submitted'), ('software_version_upgrade', 'A new version of the MUSICC system has been deployed'), ('custom', 'A custom notification')], max_length=64)),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='musiccscenario',
            name='images',
            field=models.ManyToManyField(to='musicc.ScenarioImage'),
        ),
        migrations.AddField(
            model_name='musiccscenario',
            name='open_drive',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenDrive'),
        ),
        migrations.AddField(
            model_name='musiccscenario',
            name='revision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccRevision', to_field='revision'),
        ),
        migrations.AddField(
            model_name='musiccscenario',
            name='scenario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenario'),
        ),
        migrations.AddField(
            model_name='musiccscenario',
            name='updated_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.AddField(
            model_name='musiccrevision',
            name='open_drive_revision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenDriveRevision'),
        ),
        migrations.AddField(
            model_name='musiccrevision',
            name='open_scenario_revision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenarioRevision'),
        ),
        migrations.AddField(
            model_name='musiccrevision',
            name='updated_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.CreateModel(
            name='DownloadLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('seed', models.BinaryField()),
                ('download_size', models.PositiveIntegerField()),
                ('download_type', models.CharField(choices=[('Native', 'NATIVE'), ('Non-native', 'NON-NATIVE')], max_length=16)),
                ('concrete_per_logical', models.PositiveIntegerField()),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.QueryCache')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommentControl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('label', models.CharField(max_length=255)),
                ('state', models.CharField(choices=[('LOCKED', 'LOCKED'), ('DISABLED', 'DISABLED')], max_length=16)),
                ('revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccRevision')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('message', models.CharField(max_length=256)),
                ('scenario_broken', models.BooleanField(default=False)),
                ('musicc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChangeOpenScenarioMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('filename', models.CharField(blank=True, max_length=500, null=True)),
                ('change_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog')),
                ('musicc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('record', models.ForeignKey(blank=True, db_column='open_scenario_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenario')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChangeOpenDriveMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('filename', models.CharField(blank=True, max_length=500, null=True)),
                ('change_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog')),
                ('musicc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('record', models.ForeignKey(blank=True, db_column='open_drive_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenDrive')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChangeMusiccMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('filename', models.CharField(blank=True, max_length=500, null=True)),
                ('change_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog')),
                ('record', models.ForeignKey(blank=True, db_column='musicc_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='changelog',
            name='musicc_revision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccRevision', to_field='revision'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='reverted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog'),
        ),
        migrations.AddField(
            model_name='changelog',
            name='updated_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.CreateModel(
            name='ChangeCatalogMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('filename', models.CharField(blank=True, max_length=500, null=True)),
                ('change_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog')),
                ('musicc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.MusiccScenario')),
                ('record', models.ForeignKey(blank=True, db_column='catalog_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='musicc.Catalog')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='catalogmapping',
            name='open_scenario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenario'),
        ),
        migrations.AddField(
            model_name='catalogmapping',
            name='updated_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.AddField(
            model_name='catalog',
            name='revision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.OpenScenarioRevision'),
        ),
        migrations.AddField(
            model_name='catalog',
            name='updated_by_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_date_time', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('APPROVED', 'APPROVED'), ('DENIED', 'DENIED'), ('PENDING', 'PENDING'), ('CANCELLED', 'CANCELLED')], max_length=16)),
                ('change', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicc.ChangeLog')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reviewer', to=settings.AUTH_USER_MODEL, to_field='username')),
                ('submitted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submitter', to=settings.AUTH_USER_MODEL, to_field='username')),
                ('updated_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='musiccscenario',
            constraint=models.UniqueConstraint(condition=models.Q(active=True), fields=('version', 'label', 'revision'), name='only_one_active_musicc'),
        ),
    ]
